from enum import Enum
from typing import Any, Dict, Optional

from niagads.common.models.base import CustomBaseModel
from niagads.common.search.types import MatchType
from niagads.common.types import Entity
from niagads.enums.core import CaseInsensitiveEnum
from pydantic import (
    Field,
    FieldSerializationInfo,
    field_serializer,
    model_validator,
)


class MatchedRecordDetails(CustomBaseModel):
    label: str
    description: Optional[str] = None
    annotation: Optional[Dict[str, Any]] = None


class SearchMatch(CustomBaseModel):
    matched_record_id: str = Field(
        serialization_alias="id",
        title="Record ID",
        description="unique record identifier",
    )

    matched_record_type: Entity = Field(title="Record Type")
    matched_text: str = Field(title="Matched", description="matched term or phrase")
    match_type: MatchType = Field(
        title="Match Type", description=f"type of match, one of {MatchType.list()}"
    )
    rank: int = Field(
        title="Match Rank",
        description="ranked confidence in rank (0 - exact, with decreasing confidence as rank increases) "
        "based on match type and semantic similarity score (when relevant).  "
        "Exact matches are always ranked the highest, but other rankings will depend on search strategy.",
    )
    score: Optional[float] = Field(
        default=None, title="Score", description="semantic similarity, if relevant"
    )

    matched_record_label: str

    @model_validator(mode="before")
    @classmethod
    def populate_label(cls, data: Any) -> Any:
        """Populate a missing label from the matched record details."""
        if isinstance(data, dict) and "label" not in data:
            if "matched_record_details" in data:
                details = data["matched_record_details"]
                matched_record_label = (
                    details.label
                    if isinstance(details, MatchedRecordDetails)
                    else details["label"]
                )
                return {**data, "matched_record_label": matched_record_label}
        return data

    @field_serializer("*")
    def serialize_types(self, v, _info: FieldSerializationInfo):
        """custom field handlers
        override base to always
        - return enum names instead of values
        """

        if isinstance(v, (Enum, CaseInsensitiveEnum)):
            return v.name

        return v


class AnnotatedSearchMatch(SearchMatch):
    matched_record_details: MatchedRecordDetails = Field(
        title="Qualifying or descriptive information for the record"
    )
