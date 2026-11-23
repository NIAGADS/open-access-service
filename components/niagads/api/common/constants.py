HTTP_CLIENT_TIMEOUT = 30  # timeout in seconds

# pagination
DEFAULT_PAGE_SIZE = 5000
MAX_NUM_PAGES = 100

# Responses

RESPONSES = {
    404: {"description": "Record not found"},
    422: {"description": "Parameter Validation Error"},
    429: {
        "description": (
            "Too many requests. Requests are rate limited per client IP across "
            "non-exempt endpoints using a fixed window."
        ),
        "headers": {
            "Retry-After": {
                "description": "Seconds to wait before retrying.",
                "schema": {"type": "integer"},
            },
            "X-RateLimit-Limit": {
                "description": "Maximum requests allowed in the current window.",
                "schema": {"type": "integer"},
            },
            "X-RateLimit-Remaining": {
                "description": "Requests remaining in the current window.",
                "schema": {"type": "integer"},
            },
            "X-RateLimit-Reset": {
                "description": "Unix timestamp when the rate-limit window resets.",
                "schema": {"type": "integer"},
            },
        },
    },
}


# regular expressions
SHARD_PATTERN = r"chr(\d{1,2}|[XYM]|MT)"

# default values
DEFAULT_NULL_STRING = "NA"
