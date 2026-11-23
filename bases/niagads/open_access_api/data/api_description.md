The NIAGADS Open Access API provides programmatic access to publicly available genomic data, annotations, and research resources supporting Alzheimer's disease and related dementias (AD/ADRD) research.

The API enables applications and computational workflows to retrieve, query, and integrate genetic associations, genomic variants, functional annotations, and harmonized datasets across NIAGADS Open Access resources.

## Data and API Resources

The API provides access to several complementary categories of genomic information:

- **Genes and Genomic Regions:** Gene identifiers, genomic coordinates, transcripts, and associated annotations.
- **Genetic Variants:** Annotated variants, including variants identified through the Alzheimer's Disease Sequencing Project (ADSP).
- **AD/ADRD Genetic Associations:** Curated AD/ADRD genetic associations and genome-wide association study (GWAS) results.
- **AD/ADRD GWAS Summary Statistics:** Harmonized association statistics and genomic region-based queries across available GWAS datasets.
- **Functional Genomics:** Third-party genomic annotations and functional evidence, including regulatory elements, molecular QTLs, and other functional genomics resources. **coming soon**
- **ADSP FunGen xQTLs:** molecular QTLs from the Alzheimer's Disease Sequencing Project (ADSP). **coming soon**
- **Datasets and Metadata:** Dataset descriptions, identifiers, provenance, and related metadata supporting data discovery and integration.

Endpoints are organized by resource and operation. Refer to the endpoint documentation below for supported queries, parameters, response schemas, and examples.

## Rate Limits

API requests are subject to the following limits:

| Access | General Endpoints | Service Endpoints |
| --- | --- | --- |
| Anonymous | 120 requests/minute | 120 requests/minute |
| Approved API Token* | 300 requests / minute | 300 requests / minute |
| Trusted applications | 300 requests / minute | Exempt |

_* Registered accounts with approved API tokens coming soon._

Rate limits apply to requests originating from the same client IP address.

Requests exceeding the applicable limit receive HTTP `429 Too Many Requests`. The `Retry-After` response header indicates the number of seconds to wait before retrying.

## Model Context Protocol (MCP)

The API supports the Model Context Protocol (MCP), enabling AI assistants and agents to discover and access supported API functionality through standardized tools.

### MCP Endpoint

`https://api.niagads.org/mcp`

The MCP server uses Streamable HTTP and exposes supported API endpoints as discoverable tools. No separate MCP credentials are required for publicly accessible endpoints.

### Connecting an MCP Client

Configure an MCP-compatible client using the endpoint URL above and the Streamable HTTP transport. The client handles protocol initialization, tool discovery, and tool execution.

Once connected, AI assistants and agents can discover available tools, inspect their input schemas, and submit requests using the same underlying API functionality available through REST.

### Usage Guidelines

- **Tool discovery:** Available tools and their parameters are provided automatically through MCP.
- **Rate limits:** MCP requests are subject to the API's published rate limits. Clients should handle rate-limit responses and retry appropriately.
- **Data access:** MCP tools follow the same access restrictions as their corresponding REST endpoints.
- **Documentation:** Refer to the API's endpoint documentation for detailed descriptions of supported operations, parameters, and returned data.
