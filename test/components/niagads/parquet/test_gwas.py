"""GWAS export contracts, including inclusive regional queries."""

import gzip
import subprocess
import sys

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from niagads.parquet.gwas import GWASParquetExporter

COLUMNS = [
    "chr",
    "position",
    "end",
    "length",
    "ref",
    "alt",
    "id",
    "ref_snp_id",
    "variant_class",
    "pvalue",
    "effect_direction",
    "info",
]
HEADER = "#chrom\tposition\tvariant_id\tref\talt\tpval\teffect_size\trsid"


def write_input(tmp_path, rows, extra_header=""):
    source = tmp_path / "gwas.tsv"
    source.write_text(HEADER + extra_header + "\n" + "\n".join(rows) + "\n")
    return source


def test_exports_exact_statistics_reference_spans_and_row_group_metadata(tmp_path):
    source = write_input(
        tmp_path,
        [
            "1\t10\t1:10:A:G\tA\tG\t1.23400e-1000\t-0.2\trs1",
            "1\t20\t1:20:AT:A\tAT\tA\t0.0500\t0\t.",
            "2\t1\t2:1:A:ATG\tA\tATG\t1\t0.3\trs2",
            "M\t2\tM:2:AC:GT\tAC\tGT\tNA\t.\t.",
        ],
    )
    output = tmp_path / "dataset.parquet"
    exporter = GWASParquetExporter("dataset-1", "GRCh38", batch_size=2)
    assert exporter.export(source, output) == 4
    table = pq.read_table(output)
    assert table.column_names == COLUMNS
    assert table["pvalue"].to_pylist() == ["1.23400e-1000", "0.0500", "1", "NA"]
    assert table["effect_direction"].to_pylist() == ["-", "+", "+", None]
    assert table["end"].to_pylist() == [10, 21, 1, 3]
    assert table["length"].to_pylist() == [1, 2, 1, 2]
    assert table["variant_class"].to_pylist() == [
        "SNV",
        "SHORT_DEL",
        "SHORT_INS",
        "MNV",
    ]
    assert table["ref_snp_id"].to_pylist() == ["rs1", None, "rs2", None]
    assert table["chr"].to_pylist() == ["1", "1", "2", "M"]
    assert table["id"].to_pylist()[1] == "1:20:AT:A"
    assert "pvalue=1.23400e-1000" in table["info"][0].as_py()
    assert table.schema.field("position").type == pa.int64()
    assert table.schema.field("pvalue").type == pa.string()
    assert table.schema.metadata == {
        b"dataset_id": b"dataset-1",
        b"reference_assembly": b"GRCh38",
        b"coordinate_convention": b"1-based inclusive",
        b"schema_version": b"1.0",
    }
    metadata = pq.read_metadata(output)
    assert metadata.num_row_groups == 2
    assert metadata.row_group(0).column(1).statistics.min == 10
    assert metadata.row_group(0).column(1).statistics.max == 20
    assert metadata.row_group(0).column(1).compression == "ZSTD"
    assert exporter.validate(output, expected_rows=4) == 4
    with pytest.raises(ValueError, match="row count"):
        exporter.validate(output, expected_rows=5)


def test_sv_nullable_alleles_and_inclusive_overlap_queries(tmp_path, monkeypatch):
    from niagads.ga4gh.annotators import GA4GHVRSService

    monkeypatch.setattr(
        GA4GHVRSService, "get_refget_accession", lambda self, chrom: "SQ." + "A" * 32
    )
    source = write_input(
        tmp_path,
        [
            "1\t100\t1:100:A:G\tA\tG\t1e-999\t-1\t.\t100\tSNV",
            "1\t150\t.\t.\t.\t0.1\t1\t.\t300\tDEL",
            "1\t201\t1:201:C:T\tC\tT\t0.2\t1\t.\t201\tSNV",
        ],
        "\tend\tvariant_class",
    )
    output = tmp_path / "sv.parquet"
    GWASParquetExporter(
        "sv", "GRCh38", batch_size=1, seqrepo_data_proxy="https://seqrepo.example"
    ).export(source, output)
    table = pq.read_table(output)
    assert table["ref"].to_pylist() == ["A", None, "C"]
    assert table["alt"].to_pylist() == ["G", None, "T"]
    assert table["length"].to_pylist() == [1, 151, 1]
    assert table["id"][1].as_py().startswith("DEL_CHR1_")
    for start, end, positions in [
        (100, 150, [100, 150]),
        (200, 200, [150]),
        (300, 300, [150]),
        (301, 301, []),
    ]:
        result = pq.read_table(
            output,
            filters=[("chr", "=", "1"), ("position", "<=", end), ("end", ">=", start)],
        )
        assert result["position"].to_pylist() == positions


def test_long_indel_uses_existing_generator_without_normalization(
    tmp_path, monkeypatch
):
    from niagads.ga4gh.annotators import GA4GHVRSService

    monkeypatch.setattr(
        GA4GHVRSService, "get_refget_accession", lambda self, chrom: "SQ." + "A" * 32
    )
    # Both alleles are <50 bases; their sum selects the generator's allele hash.
    ref, alt = "A" * 30, "C" * 25
    source = write_input(
        tmp_path, [f"1\t10\t1:10:{ref}:{alt}\t{ref}\t{alt}\t1e-400\t-1\t."]
    )
    output = tmp_path / "long.parquet"
    GWASParquetExporter(
        "long", "GRCh38", seqrepo_data_proxy="https://seqrepo.example"
    ).export(source, output)
    row = pq.read_table(output).to_pylist()[0]
    assert row["id"].startswith("INDEL_CHR1_")
    assert (row["ref"], row["alt"], row["position"], row["end"], row["length"]) == (
        ref,
        alt,
        10,
        39,
        30,
    )
    assert row["pvalue"] == "1e-400"


@pytest.mark.parametrize(
    "rows",
    [
        ["1\t20\t1:20:A:T\tA\tT\t1\t0\t.", "1\t10\t1:10:A:T\tA\tT\t1\t0\t."],
        ["10\t1\t10:1:A:T\tA\tT\t1\t0\t.", "2\t1\t2:1:A:T\tA\tT\t1\t0\t."],
    ],
)
def test_rejects_unsorted_input_across_batches_without_publishing(tmp_path, rows):
    source = write_input(tmp_path, rows)
    output = tmp_path / "bad.parquet"
    with pytest.raises(ValueError, match="sort"):
        GWASParquetExporter("bad", "GRCh38", batch_size=1).export(source, output)
    assert not output.exists()
    assert list(tmp_path.glob("*.tmp")) == []


def test_rejects_missing_sv_span(tmp_path):
    source = write_input(
        tmp_path, ["1\t10\t.\t.\t<DEL>\t1\t0\t.\tDEL"], "\tvariant_class"
    )
    with pytest.raises(ValueError, match="span|end|length"):
        GWASParquetExporter("sv", "GRCh38").export(source, tmp_path / "bad.parquet")


def test_rejects_bad_schema_and_corrupt_output(tmp_path):
    exporter = GWASParquetExporter("x", "GRCh38")
    output = tmp_path / "wrong.parquet"
    pq.write_table(pa.table({"position": [1]}), output)
    with pytest.raises(ValueError, match="schema"):
        exporter.validate(output, expected_rows=1)
    output.write_bytes(b"not a parquet file")
    with pytest.raises((ValueError, pa.ArrowInvalid)):
        exporter.validate(output, expected_rows=1)


def test_module_cli_reads_gzip_and_preserves_existing_info(tmp_path):
    source = tmp_path / "gwas.tsv.gz"
    with gzip.open(source, "wt") as stream:
        stream.write(
            HEADER + "\tinfo\n1\t10\t1:10:A:T\tA\tT\t1e-1000\t-1\trs1\tlabel=original\n"
        )
    output = tmp_path / "cli.parquet"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "niagads.gwas_parquet_export.core",
            "--input",
            str(source),
            "--output",
            str(output),
            "--dataset-id",
            "cli",
            "--reference-assembly",
            "GRCh38",
            "--batch-size",
            "1",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert pq.read_table(output)["info"].to_pylist() == ["label=original"]
    assert pq.read_table(output)["pvalue"].to_pylist() == ["1e-1000"]


def test_preserves_existing_output_and_cleans_up_failed_exports(tmp_path):
    source = write_input(tmp_path, ["1\t10\t1:10:A:T\tA\tT\t1e-1000\t1\t."])
    output = tmp_path / "existing.parquet"
    output.write_bytes(b"existing data")
    with pytest.raises(FileExistsError):
        GWASParquetExporter("x", "GRCh38").export(source, output)
    assert output.read_bytes() == b"existing data"


@pytest.mark.parametrize(
    "row,extra_header,error",
    [
        ("1\t0\t1:0:A:T\tA\tT\t1\t1\t.", "", "positive"),
        ("1\t10\t.\t.\t<DEL>\t1\t1\t.\t5\tDEL", "\tend\tvariant_class", "positive"),
        (
            "1\t10\t.\t.\t<DEL>\t1\t1\t.\t20\t5\tDEL",
            "\tend\tlength\tvariant_class",
            "disagree",
        ),
        ("1\t10\t1:10:A:T\tA\tT\t1\t1", "", "field count"),
        ("1\t10\t.\t.\t<DEL>\t1\t1\t.\t20\tDEL", "\tend\tvariant_class", "seqrepo"),
    ],
)
def test_rejects_malformed_input_without_output(tmp_path, row, extra_header, error):
    source = write_input(tmp_path, [row], extra_header)
    output = tmp_path / "bad.parquet"
    with pytest.raises(ValueError, match=error):
        GWASParquetExporter("x", "GRCh38").export(source, output)
    assert not output.exists()
    assert list(tmp_path.glob("*.tmp")) == []


def test_header_only_input_retains_schema(tmp_path):
    source = tmp_path / "empty.tsv"
    source.write_text(HEADER + "\n")
    output = tmp_path / "empty.parquet"
    exporter = GWASParquetExporter("empty", "GRCh38")
    assert exporter.export(source, output) == 0
    table = pq.read_table(output)
    assert table.num_rows == 0
    assert table.column_names == COLUMNS


def test_ignores_large_original_input_annotations(tmp_path):
    source = write_input(
        tmp_path,
        ["1\t10\t1:10:A:T\tA\tT\t1e-1000\t1\t.\t" + "x" * 150_000],
        "\tuser_input",
    )
    output = tmp_path / "large-annotation.parquet"
    assert GWASParquetExporter("x", "GRCh38").export(source, output) == 1
    assert pq.read_table(output).column_names == COLUMNS


def test_sequence_sv_and_symbolic_sv_use_reference_spans(tmp_path, monkeypatch):
    from niagads.ga4gh.annotators import GA4GHVRSService

    monkeypatch.setattr(
        GA4GHVRSService, "get_refget_accession", lambda self, chrom: "SQ." + "A" * 32
    )
    source = write_input(
        tmp_path,
        [
            f"1\t10\t1:10:{'A' * 50}:A\t{'A' * 50}\tA\t1e-500\t1\t.\t.\t.",
            "1\t100\t.\tN\t<DEL>\t1e-400\t1\t.\t250\tDEL",
        ],
        "\tend\tvariant_class",
    )
    output = tmp_path / "sv.parquet"
    GWASParquetExporter(
        "sv", "GRCh38", seqrepo_data_proxy="https://seqrepo.example"
    ).export(source, output)
    rows = pq.read_table(output).to_pylist()
    assert [(row["end"], row["length"]) for row in rows] == [(59, 50), (250, 151)]
    assert all(row["id"].startswith("DEL_CHR1_") for row in rows)
    assert rows[1]["alt"] == "<DEL>"


def test_validation_rejects_reordered_rows_and_changed_metadata(tmp_path):
    source = write_input(
        tmp_path,
        [
            "1\t10\t1:10:A:T\tA\tT\t1\t1\t.",
            "1\t20\t1:20:A:T\tA\tT\t1\t1\t.",
        ],
    )
    output = tmp_path / "valid.parquet"
    exporter = GWASParquetExporter("x", "GRCh38", batch_size=1)
    exporter.export(source, output)
    table = pq.read_table(output)
    bad = tmp_path / "bad.parquet"
    pq.write_table(table.take([1, 0]), bad, row_group_size=1)
    with pytest.raises(ValueError, match="sorted"):
        exporter.validate(bad, expected_rows=2)
    pq.write_table(table.replace_schema_metadata({b"dataset_id": b"other"}), bad)
    with pytest.raises(ValueError, match="metadata"):
        exporter.validate(bad, expected_rows=2)
