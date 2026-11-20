# Repository Hooks

This directory contains scripts supporting automated repository maintenance, validation, and resource generation through Git commit hooks.

Hooks are managed at the monorepo level and may operate across components, bases, and projects.

The `pre-commit` framework was selected over native Git hooks to avoid maintaining custom orchestration and file-filtering logic. It supports centralized configuration, reuse of the existing Poetry environment, and straightforward extension as repository automation needs grow.

## Implementation Guidelines

- Hooks should be lightweight and primarily responsible for orchestrating existing functionality.
- Hooks may use existing monorepo components and utilities where relevant.
- Underlying operations should be independently executable to support manual invocation, testing, and CI workflows.
- Hooks that generate version-controlled resources should produce deterministic outputs.

## Configuration

Hook registration, execution conditions, and configuration are managed through the repository-level [.pre-commit-config.yaml](../.pre-commit-config.yaml).

Install the `pre-commit` CLI and register the hooks from the repository root with
`pre-commit install`. The schema hook uses the existing root Poetry environment.

## Available Hooks

### `generate_record_schemas.py`

The hook generates validation schemas for common models defining `Records`.

Schemas are stored under `generated-resources/schemas/`, mirroring the source
package directories (without the `components/niagads/` prefix). Each model has a snake-case
filename, such as `common/gene/models/gene_record.schema.json`.

Generation is skipped when all staged paths are under `bases/`, `test/`, `tests/`,
or the `api`, `database`, `etl`, `requests`, and `postgres_dbi` components. Any other
staged path triggers generation and comparison of all record schemas. Existing
files are compared as parsed JSON, so formatting and object key order do not
trigger writes. Missing files are created and differing schemas are overwritten.

The generator reads the working tree and automatically stages schemas it creates
or updates so they are included in the commit.

Run generation manually from the repository root with
`poetry run python hooks/generate_record_schemas.py`. This also stages any schemas
it creates or updates. The command exits with status 0 on success.
