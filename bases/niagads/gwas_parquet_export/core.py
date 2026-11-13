"""Export one standardized hipFG GWAS file to Parquet."""

import argparse
from pathlib import Path

from niagads.common.core import ComponentBaseMixin
from niagads.parquet.gwas import GWASParquetExporter


class GWASParquetExport(ComponentBaseMixin):
    """Encapsulate the GWAS export command-line script."""

    def run(self, argv: list[str] | None = None) -> int:
        """Parse command-line arguments and export the selected dataset.

        Args:
            argv (list[str] | None): Arguments, or the process command line.

        Returns:
            int: Number of rows exported.
        """
        parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
        parser.add_argument(
            "--input", type=Path, required=True, help="Sorted hipFG TSV input"
        )
        parser.add_argument(
            "--output", type=Path, required=True, help="New Parquet output file"
        )
        parser.add_argument("--dataset-id", required=True)
        parser.add_argument(
            "--reference-assembly", choices=["GRCh37", "GRCh38"], required=True
        )
        parser.add_argument("--batch-size", type=int, default=100_000)
        parser.add_argument(
            "--seqrepo-data-proxy", help="SeqRepo URL/cache for SV and long-indel IDs"
        )
        args = parser.parse_args(argv)
        exporter = GWASParquetExporter(
            dataset_id=args.dataset_id,
            reference_assembly=args.reference_assembly,
            batch_size=args.batch_size,
            seqrepo_data_proxy=args.seqrepo_data_proxy,
        )
        return exporter.export(args.input, args.output)


def main() -> None:
    """Execute the class-encapsulated export script."""
    GWASParquetExport().run()


if __name__ == "__main__":
    main()
