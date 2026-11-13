from niagads.api.common.services.base import BaseEndpointService
from niagads.database.genomicsdb.schema.reference.ontology import OntologyTerm as OTOrm


class OntologyEndpointService(BaseEndpointService):
    _orm_model = OTOrm

    async def _keyword_search(self):
        namespace = self._parameters.namespace
        include_ontology = [namespace] if namespace and namespace != "" else None
        self.logger.debug(
            f"INCLUDE ONTOLOGY: {include_ontology} / namespace={namespace}"
        )
        return await super()._keyword_search(include_ontology=include_ontology)
