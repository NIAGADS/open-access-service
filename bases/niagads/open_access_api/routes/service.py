"""JSON service endpoints for external applications."""

from re import IGNORECASE
from typing import Union

from fastapi import APIRouter, Depends, Query
from niagads.api.common.models.context.request import Parameters
from niagads.api.common.models.context.response import ResponseConfiguration
from niagads.api.common.models.responses.records import RecordResponse
from niagads.api.common.parameters.location import flank_param
from niagads.api.common.parameters.response.response import data_response_content_param
from niagads.api.common.services.gene import GeneEndpointService
from niagads.api.common.services.ontology import OntologyEndpointService
from niagads.api.common.services.variant import VariantEndpointService
from niagads.api.common.types import ResponseContent, ResponseFormat
from niagads.common.search.models.record import AnnotatedSearchMatch, SearchMatch
from niagads.open_access_api.dependencies import OpenAccessEndpointContext
from niagads.utils.regular_expressions import RegularExpressions
from niagads.utils.string import matches

router = APIRouter(prefix="/service", tags=["Service"])


@router.get(
    "/feature",
    summary="Get feature location",
    description="Resolve a gene or variant identifier to one-based coordinates.",
    operation_id="getFeatureLocation",
)
async def get_feature_location(
    id: str = Query(
        description=(
            "Gene symbol, Ensembl gene ID, positional variant ID, "
            "NIAGADS structural variant ID, or RefSNP ID."
        )
    ),
    flank: int = Depends(flank_param),
    context: OpenAccessEndpointContext = Depends(),
) -> dict[str, str | int]:

    is_variant = any(
        matches(pattern, id, flags=IGNORECASE)
        for pattern in (
            RegularExpressions.POSITIONAL_VARIANT_ID,
            RegularExpressions.STRUCTUAL_VARIANT_ID,
            RegularExpressions.REF_SNP_ID,
        )
    )
    # FIXME: cache responses
    service_class = VariantEndpointService if is_variant else GeneEndpointService
    service = service_class(
        context=context,
        parameters=Parameters(id=id, flank=flank),
        response_config=None,
    )
    location = await service.get_feature_location(id, flank=flank)
    return {
        "chr": str(location.chromosome),
        "start": location.start,
        "end": location.end,
    }


@router.get(
    "/ontology-lookup",
    summary="Lookup ontology terms",
    description="Find (exact or fuzzy) matching ontology terms in a (optional) specific ontology namespace.",
    operation_id="keywordSearchOntologyTerm",
    response_model=Union[
        RecordResponse[AnnotatedSearchMatch], RecordResponse[SearchMatch]
    ],
    openapi_extra={"x-status": "beta"},
)
async def search_ontology_term(
    keyword: str = Query(
        title="Term or CURIE (id) to match",
        description=(
            "Ontology term or partial phrase to search for. Matches are fuzzy and case insensitive."
        ),
        examples=["Alzheimer", "apolipoprotein E", "GO:0008150"],
    ),
    # TODO: extract out namespace parameter - it is also used in /query/ontology endpoint
    namespace: str = Query(
        default=None,
        title="Ontology Namespace",
        description=("Optional ontology namespace to scope the query."),
        examples=["GO", "MeSH", "MONDO", "HP"],
    ),
    content: ResponseContent = Depends(data_response_content_param),
    context: OpenAccessEndpointContext = Depends(),
) -> Union[RecordResponse[AnnotatedSearchMatch], RecordResponse[SearchMatch]]:

    service = OntologyEndpointService(
        context=context,
        parameters=Parameters(keyword=keyword, namespace=namespace),
        response_config=ResponseConfiguration(
            format=ResponseFormat.JSON,
            content=content,
            response_model=RecordResponse,
            record_model=(
                AnnotatedSearchMatch if content == ResponseContent.FULL else SearchMatch
            ),
        ),
    )

    result = await service.get_cached_response()
    from_cache = True
    if not result:
        result = await service._keyword_search()
        from_cache = False
    response = await service.generate_response(result, from_cache=from_cache)
    return response
