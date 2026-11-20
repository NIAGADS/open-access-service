# Generated Resources

This directory contains automatically generated, version-controlled resources intended for consumption by external applications, services, and integrations. These resources are made available directly through the GitHub repository without requiring installation of the associated Python packages.

Resources are organized by type, with subsequent directory structures mirroring the source package hierarchy to maintain traceability to their originating definitions.

## Resource Types

- `schemas/`: JSON Schema definitions generated from Pydantic models.

## Generation and Maintenance

Resources are generated through [repository commit hooks](../hooks/README.md) to maintain consistency with their source definitions.

- Generated files must not be edited manually.
- Changes should be made to the corresponding source definitions and propagated through the generation process.
- Generation must be deterministic to minimize unnecessary changes to version-controlled files.
- Resource paths should remain stable wherever possible to support external integrations.

## External Access

External consumers may retrieve resources directly through GitHub's raw content URLs. Use a branch reference to access current definitions or a release tag or commit SHA to reference a specific version.
