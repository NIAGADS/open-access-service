# GWAS Parquet Export Implementation Plan

## Objective and scope

Implement a reusable batch Parquet exporter in the existing `niagads.parquet`
component and a class-encapsulated `niagads.gwas_parquet_export` CLI base.
Use the root Poetry environment. Leave `projects/` and Poetry script entries
untouched. Register only the new base's package and brick mappings in root
`pyproject.toml`; the Parquet component is already registered.

The user's latest corrections supersede the original all-fields requirement:
export exactly `chr, position, end, length, ref, alt, id, ref_snp_id,
variant_class, pvalue, effect_direction, info`, in that order.
Copy hipFG `pval` verbatim into string `pvalue`; calculate string direction
from the effect-size sign as in the GWAS ETL plugin. Ignore other statistical
fields. Never parse p-values numerically or repeat statistical harmonization.

## Approach and dependencies

Use PyArrow, ZSTD, fixed-size batches, and native row-group statistics to write
one file. Validate row counts, schema, natural chromosome/position order across
batches, and output integrity without sorting. Metadata holds dataset ID,
reference assembly, 1-based inclusive coordinates, and schema version.
Reference span is `end - position + 1`, derived from reference sequence for
ordinary alleles; symbolic/null-allele SVs require explicit end or span length.
Reuse `PrimaryKeyGenerator` only for SVs and long indels, with normalization
and reference validation disabled. Reuse chromosome/build enums, variant models,
compressed-file opener, annotation-string utility, and `ComponentBaseMixin`.
Keep existing shared model semantics unchanged. The database loading base is
not an export entry point and will not be changed.

## Implementation steps

- [ ] Write focused tests in `test/components/niagads/parquet/test_gwas.py` for
  ordinary variants, nullable SV alleles, long indels, tiny p-value strings,
  direction, schema/order/metadata, multiple batches, invalid order and spans,
  row-count/integrity validation, and inclusive PyArrow regional overlaps.
  Run them first to establish the missing implementation failure.
- [ ] Implement `GWASParquetExporter` in `components/niagads/parquet/gwas.py`
  with `export(input_file, output_file) -> int` and streaming validation.
  Require dataset ID and assembly; expose batch size and SeqRepo setting.
  Preserve existing output on failure and remove temporary output.
- [ ] Add `bases/niagads/gwas_parquet_export/{__init__,core}.py`, with a
  class-based CLI and module execution via `python -m ...core`; register its
  root package/brick only. Document input/output, options, and command in its
  README. Add an actual CLI invocation test.
- [ ] Run the focused tests and Black/isort checks in the root environment;
  review the diff and confirm no changes under `projects/` or script entries.
- [ ] Record verified milestones in timestamped checkpoints, create a session
  handoff, and update the shared index with status and links.

## Validation and review focus

Tests use real PyArrow files and filters. Stub only SeqRepo accession lookup
for deterministic offline primary-key generation. Check cross-batch ordering,
inclusive overlap boundaries, explicit SV spans, byte-for-byte p-value text,
null alleles, and cleanup when validation fails. Do not build any projects,
initialize other environments, launch subagents, or expand into database tests.
No further project/deployment work is authorized by this task.
