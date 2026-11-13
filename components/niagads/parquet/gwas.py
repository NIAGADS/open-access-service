"""Batch export of standardized hipFG GWAS records to a single Parquet file."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pyarrow as pa
import pyarrow.parquet as pq
from niagads.common.core import ComponentBaseMixin
from niagads.common.variant.models.record import VariantRecord
from niagads.common.variant.types import VariantClass
from niagads.ga4gh.annotators import PrimaryKeyGenerator
from niagads.genome_reference.human import GenomeBuild, HumanGenome
from niagads.utils.string import dict_to_info_string
from niagads.utils.sys import read_open_ctx
from pydantic import model_validator

GWAS_SCHEMA = pa.schema(
    [
        pa.field("chr", pa.string(), nullable=False),
        pa.field("position", pa.int64(), nullable=False),
        pa.field("end", pa.int64(), nullable=False),
        pa.field("length", pa.int64(), nullable=False),
        pa.field("ref", pa.string()),
        pa.field("alt", pa.string()),
        pa.field("id", pa.string(), nullable=False),
        pa.field("ref_snp_id", pa.string()),
        pa.field("variant_class", pa.string(), nullable=False),
        pa.field("pvalue", pa.string(), nullable=False),
        pa.field("effect_direction", pa.string()),
        pa.field("info", pa.string(), nullable=False),
    ]
)
MISSING = frozenset(("", ".", "NA"))
CHROMOSOME_ORDER = {
    chromosome.value.replace("MT", "M"): index
    for index, chromosome in enumerate(HumanGenome)
}


class _ExportVariantRecord(VariantRecord):
    """Adapt the shared ID-generator record to nullable alleles and reference span.

    Keep the shared class inference for sequence alleles. Explicit structural
    classes and spans must survive unchanged; the shared model otherwise uses
    allele-length difference and cannot accept nullable structural alleles.
    """

    id: str
    ref: str | None
    alt: str | None
    variant_class: VariantClass | None = None

    @model_validator(mode="after")
    def resolve_variant_type(self):
        """Preserve an explicit class, or use the shared sequence classifier."""
        if self.variant_class is not None:
            return self
        if self.ref is None or self.alt is None or self.alt.startswith("<"):
            raise ValueError("Nullable or symbolic alleles require variant_class")
        return super().resolve_variant_type()

    def _resolve_length(self):
        """Use an explicit reference span, or the reference sequence length."""
        if self.length is None:
            if self.ref is None or self.alt is None or self.alt.startswith("<"):
                raise ValueError("Nullable or symbolic alleles require end or length")
            self.length = len(self.ref)
        if self.position < 1 or self.length < 1:
            raise ValueError("Position and reference-span length must be positive")
        return self


class GWASParquetExporter(ComponentBaseMixin):
    """Write and validate one GWAS file with bounded batch memory."""

    def __init__(
        self,
        dataset_id: str,
        reference_assembly: str,
        batch_size: int = 100_000,
        seqrepo_data_proxy: str | None = None,
        debug: bool = False,
    ):
        """Configure export metadata, batch size, and optional ID-generation access.

        Args:
            dataset_id (str): Dataset identifier embedded in file metadata.
            reference_assembly (str): GRCh37 or GRCh38 reference assembly.
            batch_size (int): Maximum rows per batch and row group.
            seqrepo_data_proxy (str | None): SeqRepo URL or local cache path;
                required only when generating SV or long-indel IDs.
            debug (bool): Enable debug logging.
        """
        super().__init__(debug=debug)
        if not dataset_id.strip():
            raise ValueError("dataset_id must not be empty")
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        self._assembly = GenomeBuild(reference_assembly)
        self._batch_size = batch_size
        self._seqrepo_data_proxy = seqrepo_data_proxy
        self._pk_generator: PrimaryKeyGenerator | None = None
        self._schema = GWAS_SCHEMA.with_metadata(
            {
                "dataset_id": dataset_id,
                "reference_assembly": str(self._assembly),
                "coordinate_convention": "1-based inclusive",
                "schema_version": "1.0",
            }
        )

    def _convert_row(self, entry: dict[str, str]) -> dict:
        """Select variant fields and derive only spans, IDs, and effect direction.

        Args:
            entry (dict[str, str]): One standardized hipFG row.

        Returns:
            dict: Values in the export schema, with p-value text untouched.
        """
        position = int(entry["position"])
        end = int(entry["end"]) if entry.get("end", "") not in MISSING else None
        length = (
            int(entry["length"]) if entry.get("length", "") not in MISSING else None
        )
        if end is not None:
            span_length = end - position + 1
            if length is not None and length != span_length:
                raise ValueError("end and length disagree on reference span")
            length = span_length

        variant = _ExportVariantRecord(
            id=entry["variant_id"],
            chromosome=HumanGenome(entry["chrom"]),
            position=position,
            length=length,
            ref=None if entry["ref"] in MISSING else entry["ref"],
            alt=None if entry["alt"] in MISSING else entry["alt"],
            variant_class=(
                VariantClass(entry["variant_class"])
                if entry.get("variant_class", "") not in MISSING
                else None
            ),
            positional_id=f"{entry['chrom']}:{position}:{entry['ref']}:{entry['alt']}",
        )
        requires_id = variant.variant_class.is_structural_variant() or (
            variant.variant_class.is_short_indel()
            and variant.ref is not None
            and variant.alt is not None
            and len(variant.ref) + len(variant.alt) > 50
        )
        if requires_id:
            if self._pk_generator is None:
                if not self._seqrepo_data_proxy:
                    raise ValueError(
                        "SV/long-indel ID generation requires seqrepo_data_proxy"
                    )
                self._pk_generator = PrimaryKeyGenerator(
                    self._assembly, self._seqrepo_data_proxy, logger=self.logger
                )
            self._pk_generator.set_primary_key(variant, require_validation=False)
        elif variant.id in MISSING:
            raise ValueError("Conventional variants require an existing variant_id")

        effect_size = entry.get("effect_size", "")
        direction = None
        if effect_size not in MISSING:
            direction = "-" if float(effect_size) < 0 else "+"

        row = {
            "chr": variant.chromosome.value.replace("MT", "M"),
            "position": position,
            "end": position + variant.length - 1,
            "length": variant.length,
            "ref": variant.ref,
            "alt": variant.alt,
            "id": variant.id,
            "ref_snp_id": None if entry.get("rsid", "") in MISSING else entry["rsid"],
            "variant_class": str(variant.variant_class),
            "pvalue": entry["pval"],
            "effect_direction": direction,
        }
        row["info"] = (
            entry["info"]
            if "info" in entry
            else dict_to_info_string(
                {
                    key: row[key]
                    for key in ("id", "variant_class", "pvalue", "effect_direction")
                }
            )
        )
        return row

    def export(self, input_file: str | Path, output_file: str | Path) -> int:
        """Stream a hipFG TSV into one validated Parquet file.

        Args:
            input_file (str | Path): Sorted TSV, optionally gzip/bzip2 compressed.
            output_file (str | Path): New output filename in an existing directory.

        Returns:
            int: Number of exported rows.

        Raises:
            ValueError: Input schema, coordinates, or ordering are invalid.
            FileExistsError: The output already exists; it is never overwritten.
        """
        output = Path(output_file)
        if output.exists():
            raise FileExistsError(output)
        with NamedTemporaryFile(
            dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
        count = 0
        try:
            with (
                read_open_ctx(str(input_file)) as stream,
                pq.ParquetWriter(
                    temporary,
                    self._schema,
                    compression="zstd",
                    write_statistics=True,
                    write_page_checksum=True,
                ) as writer,
            ):
                header_line = next(stream, None)
                if not header_line:
                    raise ValueError("Missing hipFG header")
                header = header_line.rstrip("\r\n").split("\t")
                header[0] = header[0].lstrip("#")
                required = {"chrom", "position", "variant_id", "ref", "alt", "pval"}
                if len(set(header)) != len(header) or not required.issubset(header):
                    raise ValueError(
                        "Invalid hipFG schema: duplicate or missing required fields"
                    )
                batch = []
                for line_number, line in enumerate(stream, start=2):
                    values = line.rstrip("\r\n").split("\t")
                    if len(values) != len(header):
                        raise ValueError(
                            f"Line {line_number}: field count differs from header"
                        )
                    try:
                        batch.append(self._convert_row(dict(zip(header, values))))
                    except ValueError as error:
                        raise ValueError(f"Line {line_number}: {error}") from error
                    if len(batch) == self._batch_size:
                        writer.write_table(
                            pa.Table.from_pylist(batch, schema=self._schema)
                        )
                        count += len(batch)
                        batch.clear()
                if batch:
                    writer.write_table(pa.Table.from_pylist(batch, schema=self._schema))
                    count += len(batch)
            self.validate(temporary, expected_rows=count)
            os.link(temporary, output)
        finally:
            temporary.unlink(missing_ok=True)
        return count

    def validate(self, file: str | Path, expected_rows: int) -> int:
        """Decode batches and verify schema, metadata, spans, sorting, and count.

        Args:
            file (str | Path): Parquet file to validate.
            expected_rows (int): Row count observed in the source stream.

        Returns:
            int: Verified number of rows.

        Raises:
            ValueError: Schema, row count, coordinates, or ordering are invalid.
            pa.ArrowInvalid: Parquet contents cannot be decoded or verified.
        """
        count = 0
        previous = None
        with pq.ParquetFile(file, page_checksum_verification=True) as parquet:
            if not parquet.schema_arrow.equals(self._schema, check_metadata=True):
                raise ValueError(
                    "Parquet schema or metadata differs from export schema"
                )
            if parquet.metadata.num_rows != expected_rows:
                raise ValueError("Parquet row count differs from input row count")
            for batch in parquet.iter_batches(batch_size=self._batch_size):
                batch.validate(full=True)
                for field, column in zip(self._schema, batch.columns):
                    if not field.nullable and column.null_count:
                        raise ValueError(f"Null value in required field {field.name}")
                for chromosome, position, end, length in zip(
                    batch.column("chr").to_pylist(),
                    batch.column("position").to_pylist(),
                    batch.column("end").to_pylist(),
                    batch.column("length").to_pylist(),
                ):
                    if chromosome not in CHROMOSOME_ORDER:
                        raise ValueError(f"Invalid chromosome {chromosome}")
                    if position < 1 or end < position or length != end - position + 1:
                        raise ValueError(
                            "Invalid inclusive coordinates or reference span"
                        )
                    current = (CHROMOSOME_ORDER[chromosome], position)
                    if previous is not None and current < previous:
                        raise ValueError(
                            "GWAS rows are not sorted by chromosome and position"
                        )
                    previous = current
                count += batch.num_rows
        if count != expected_rows:
            raise ValueError("Decoded row count differs from input row count")
        return count
