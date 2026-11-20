"""Generate the repository's record JSON schemas."""

import ast
import json
import subprocess
import sys
from importlib import import_module
from pathlib import Path
from typing import Any

from niagads.common.core import ComponentBaseMixin
from niagads.common.models.base import CustomBaseModel
from niagads.common.reference.ontologies.types import BiosampleType
from niagads.enums.core import CaseInsensitiveEnum
from niagads.utils.string import to_snake_case
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import core_schema


class EnumNameJsonSchemaGenerator(GenerateJsonSchema, ComponentBaseMixin):
    """Represent custom enum names and minimal biosample ontology terms."""

    def enum_schema(self, schema: core_schema.EnumSchema) -> JsonSchemaValue:
        """Use biosample term objects and CaseInsensitiveEnum member names."""
        json_schema = super().enum_schema(schema)
        if schema["cls"] is BiosampleType:
            json_schema["type"] = "object"
            json_schema["enum"] = [
                member.value.model_dump(mode="json", include={"term", "curie"})
                for member in schema["members"]
            ]
        elif issubclass(schema["cls"], CaseInsensitiveEnum):
            json_schema["type"] = "string"
            json_schema["enum"] = [member.name for member in schema["members"]]
        return json_schema

    def encode_default(self, dft: Any) -> Any:
        """Encode biosample defaults as term objects and custom enums by name."""
        if isinstance(dft, BiosampleType):
            return dft.value.model_dump(mode="json", include={"term", "curie"})
        if isinstance(dft, CaseInsensitiveEnum):
            return dft.name
        return super().encode_default(dft)


class RecordSchemaGenerator(ComponentBaseMixin):
    """Discover record models and update their JSON schema resources."""

    def __init__(self, source_directory: Path, output_directory: Path):
        """Initialize source and destination directories.

        Args:
            source_directory (Path): Root of the niagads.common source package.
            output_directory (Path): Corresponding generated schema directory.
        """
        super().__init__()
        self._source_directory = source_directory
        self._output_directory = output_directory

    def generate(self) -> list[Path]:
        """Generate validation schemas and write missing or changed resources.

        Discover locally defined CustomBaseModel subclasses whose names end in
        Record in the common package. Compare parsed JSON to preserve existing
        formatting when schema content is unchanged.

        Returns:
            list[Path]: Paths of newly created or updated schema files.
        """
        schemas: dict[Path, dict] = {}
        for source in sorted(self._source_directory.rglob("*.py")):
            definitions = ast.parse(
                source.read_text(encoding="utf-8"), filename=str(source)
            )
            names = [
                node.name
                for node in definitions.body
                if isinstance(node, ast.ClassDef) and node.name.endswith("Record")
            ]
            if not names:
                continue

            relative_path = source.relative_to(self._source_directory)
            module_name = ".".join(
                ("niagads", "common", *relative_path.with_suffix("").parts)
            )
            module = import_module(module_name)
            for name in names:
                model = getattr(module, name)
                if not issubclass(model, CustomBaseModel):
                    continue

                destination = (
                    self._output_directory
                    / relative_path.parent
                    / f"{to_snake_case(name)}.schema.json"
                )
                schemas[destination] = model.model_json_schema(
                    mode="validation", schema_generator=EnumNameJsonSchemaGenerator
                )

        changed = []
        for destination, schema in schemas.items():
            if destination.exists():
                existing = json.loads(destination.read_text(encoding="utf-8"))
                if existing == schema:
                    continue

            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            changed.append(destination)

        return changed


def main() -> int:
    """Generate and stage updated schemas relative to the repository root."""
    root = Path(__file__).resolve().parents[1]
    generator = RecordSchemaGenerator(
        source_directory=root / "components" / "niagads" / "common",
        output_directory=root / "generated-resources" / "schemas" / "common",
    )
    changed = generator.generate()
    for path in changed:
        print(f"Updated {path.relative_to(root)}")
    if changed:
        subprocess.run(
            ["git", "add", "--", *(str(path.relative_to(root)) for path in changed)],
            cwd=root,
            check=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
