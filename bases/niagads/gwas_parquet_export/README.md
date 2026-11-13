# GWAS Parquet export

Export an existing standardized hipFG summary-statistics TSV as one Parquet
file. Input must already be sorted in chromosome order 1–22, X, Y, M, then by
position. The exporter checks order but never sorts, partitions, filters rows,
normalizes alleles, maps rsIDs, or harmonizes statistics.

From the monorepo root, using its existing Poetry environment:

```bash
poetry run python -m niagads.gwas_parquet_export.core \
  --input /data/harmonized-gwas.tsv.gz \
  --output /data/dataset.parquet \
  --dataset-id DATASET_ID \
  --reference-assembly GRCh38
```

The script is `bases/niagads/gwas_parquet_export/core.py`, encapsulated in
`GWASParquetExport`. No Poetry CLI script entry or deployable project is added.
The reusable implementation is `niagads.parquet.gwas.GWASParquetExporter`.
Use `--help` for arguments. `--batch-size` defaults to 100,000 rows and controls
batch memory and row-group size. The output directory must exist. Existing
output files are never overwritten.

## Input

Use the GWAS ETL plugin's hipFG header convention, optionally starting with
`#chrom`. Plain text, `.gz`, and `.bz2` files are supported by the shared opener.

Required columns: `chrom`, `position`, `variant_id`, `ref`, `alt`, `pval`.
`effect_size` supplies the effect direction; missing values produce null.
`rsid` supplies `ref_snp_id`; a missing column or value produces null.
Empty strings, `.`, and `NA` denote missing alleles, rsIDs, and optional fields.
P-values are the exception: their text, including missing markers, is copied
verbatim, with no numeric conversion, rounding, or significance filtering.
Other hipFG columns are ignored.

Optional `variant_class` uses the existing `VariantClass` names (for example
`SNV`, `SHORT_DEL`, `DEL`, `DUP`, `INV`). Sequence alleles without a class use
the existing variant model's classification. Nullable/symbolic alleles require
an explicit class and an `end` or `length` column describing their reference
span. `end` is inclusive; `length` is a positive reference span, not SVLEN or
allele-length change. When both are given, they must agree. Otherwise the
reference span is the reference sequence length, including any anchor base.
Insertions with a one-base reference allele therefore span one reference base.

Conventional `variant_id` values are preserved. SVs and long indels use the
existing `PrimaryKeyGenerator` conventions. For files containing them, supply
the same SeqRepo URL or cache used by the annotation tools:

```bash
poetry run python -m niagads.gwas_parquet_export.core \
  --input /data/harmonized-gwas.tsv.gz \
  --output /data/dataset.parquet \
  --dataset-id DATASET_ID --reference-assembly GRCh38 \
  --seqrepo-data-proxy /data/seqrepo
```

SeqRepo is initialized only if needed for ID generation. These calls disable
reference validation and normalization; a conventional-only file needs no
SeqRepo. The generator treats structural classes (including sequence alleles
of at least 50 bases) as structural IDs; short-indel alleles with combined
length over 50 use its allele-hash convention. Nullable alleles remain null.
SeqRepo lookup failures propagate and do not publish a partial output.

## Output

Column order is fixed:

| Column | Arrow type | Meaning |
| --- | --- | --- |
| `chr` | string | 1–22, X, Y, M; chromosome aliases follow `HumanGenome` |
| `position` | int64 | 1-based inclusive start |
| `end` | int64 | 1-based inclusive end |
| `length` | int64 | Reference span: `end - position + 1` |
| `ref` | nullable string | Reference allele |
| `alt` | nullable string | Alternate allele |
| `id` | string | Existing positional ID or generated structural/long-indel ID |
| `ref_snp_id` | nullable string | Existing rsID, without mapping |
| `variant_class` | string | Existing variant-class convention |
| `pvalue` | string | Exact hipFG `pval` text, including values such as `1e-1000` |
| `effect_direction` | nullable string | `-` for negative effect size, `+` otherwise, following the GWAS ETL rule |
| `info` | string | Supplied `info` verbatim, or `key=value;...` annotations for ID, class, p-value, and direction |

The file uses ZSTD compression, native row-group statistics, and page checksums.
Schema metadata contains `dataset_id`, `reference_assembly` (GRCh37/GRCh38),
`coordinate_convention` (`1-based inclusive`), and `schema_version` (`1.0`).
After writing, validation decodes batches and verifies checksums, schema,
metadata, row count, coordinate spans, nullability, and sorting across row
groups. Only the validated file becomes the final output.

For inclusive regional overlaps, both start and end matter:

```python
import pyarrow.parquet as pq

region = pq.read_table(
    "/data/dataset.parquet",
    filters=[("chr", "=", "1"), ("position", "<=", 200), ("end", ">=", 100)],
)
```

This includes variants starting before the region but extending into it.
