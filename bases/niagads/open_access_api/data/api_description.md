The NIAGADS Open Access API provides programmatic access to publicly available genomic data, annotations, and research resources supporting Alzheimer's disease and related dementias (AD/ADRD) research.

The API enables applications and computational workflows to retrieve, query, and integrate genetic associations, genomic variants, functional annotations, and harmonized datasets across NIAGADS Open Access resources.

## Data and API Resources

The API provides access to several complementary categories of genomic information:

- **Genes and Genomic Regions:** Gene identifiers, genomic coordinates, transcripts, and associated annotations.
- **Genetic Variants:** Annotated variants, including variants identified through the Alzheimer's Disease Sequencing Project (ADSP).
- **AD/ADRD Genetic Associations:** Curated AD/ADRD genetic associations and genome-wide association study (GWAS) results.
- **AD/ADRD GWAS Summary Statistics:** Harmonized association statistics and genomic region-based queries across available GWAS datasets.
- **Functional Genomics:** Third-party genomic annotations and functional evidence, including regulatory elements, molecular QTLs, and other functional genomics resources.
- **Datasets and Metadata:** Dataset descriptions, identifiers, provenance, and related metadata supporting data discovery and integration.

Endpoints are organized by resource and operation. Refer to the endpoint documentation below for supported queries, parameters, response schemas, and examples.

## Rate Limits

API requests are subject to the following limits:

| Access | General Endpoints | Service Endpoints |
| --- | --- | --- |
| Anonymous | 120 requests/minute | 120 requests/minute |
| Registered Account* | 300 requests / minute | 300 requests / minute |
| Trusted applications | 300 requests / minute | Exempt |

_* Registered accounts coming soon._

Rate limits apply to requests originating from the same client IP address.

Requests exceeding the applicable limit receive HTTP `429 Too Many Requests`. The `Retry-After` response header indicates the number of seconds to wait before retrying.
