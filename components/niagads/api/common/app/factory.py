import hashlib
import hmac
from io import StringIO

from niagads.api.common.app.middleware import verify_internal_proxy
import yaml
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from niagads.api.common.app.types import AppMetadata
from niagads.api.common.config import Settings
from niagads.api.common.constants import RESPONSES
from niagads.api.common.exception_handlers import (
    add_database_exception_handler,
    add_not_implemented_exception_handler,
    add_request_validation_exception_handler,
    add_runtime_exception_handler,
    add_system_exception_handler,
)
from niagads.common.core import ComponentBaseMixin
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.types import Lifespan


def rate_limit_key(request: Request) -> str:
    """get identifier used to track how many requests a a specific client makes
    within a set time window
    supported:
        - anonymous: client ip
        - registered (trusted apps, approved token) - token
        - mcp_client_id: forwarded client id or token

    # TODO: token support - identify must be derived from validated token (not token itself)
    """
    client_id = getattr(request.state, "mcp_client_id", None)
    if client_id:
        return f"mcp:{client_id}"

    client_ip = getattr(
        request.state, "verified_client_ip", None
    ) or get_remote_address(request)
    return f"ip:{client_ip}"


class AppFactory(ComponentBaseMixin):
    """Class that to creates and configures a FastAPI application
    for a NIAGADS Open Access API microservice."""

    def __init__(
        self,
        metadata: AppMetadata,
        env: str,
        lifespan: Lifespan[FastAPI] | None = None,
    ):
        """
        Initializes the AppFactory

        Args:
            metadata (OpenAPISpec): APP metadata
            env (str): production or development environment
            namespace (str, optional): for openapi specification x-namespace arg. Defaults to 'root'
            version (bool, optional): add API major  version to path.  Defaults to False
        """
        super().__init__()

        self._app: FastAPI = self._initialize_app(metadata, lifespan)
        self._app.state.signing_secret = Settings.from_env().SIGNING_SECRET.encode(
            "utf-8"
        )
        self._initialize_rate_limiter()
        self._add_middleware()
        self._add_exception_handlers()

    @property
    def app(self) -> FastAPI:
        """get the application object"""
        self._verify_app()
        return self._app

    def _verify_app(self):
        if not self._app:
            raise RuntimeError("Application is not initialized.")

    def _initialize_rate_limiter(self):
        settings = Settings.from_env()

        cache_uri = settings.CACHE_DB_URI
        if cache_uri.startswith("keydb"):
            cache_uri = cache_uri.replace("keydb", "redis")
        if cache_uri.startswith("valkey"):
            cache_uri = cache_uri.replace("valkey", "redis")

        self._limiter = Limiter(
            key_func=rate_limit_key,
            application_limits=[settings.API_RATE_LIMIT],
            storage_uri=cache_uri,
            key_prefix="open-access:ratelimit",
            strategy="fixed-window",
            headers_enabled=True,
            retry_after="delta-seconds",
            swallow_errors=False,
            in_memory_fallback_enabled=False,
        )

        self._app.state.limiter = self._limiter

    def _initialize_app(
        self,
        metadata: AppMetadata,
        lifespan: Lifespan[FastAPI] | None = None,
    ) -> FastAPI:
        """Creates the application"""

        return FastAPI(
            title=metadata.title,
            description=metadata.description,
            summary=metadata.summary,
            version=Settings.from_env().API_VERSION or "0.0.1",
            # terms_of_service= # FIXME: review and add terms of service
            contact={
                "name": "NIAGADS Support",
                "email": Settings.from_env().ADMIN_EMAIL,
            },
            license_info={
                "name": "Apache 2.0",
                "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
            },
            servers=[{"url": Settings.from_env().API_PUBLIC_URL}],
            swagger_ui_parameters={
                "apisSorter": "alpha",
                "operationsSorter": "alpha",
                "tagsSorter": "alpha",
            },
            openapi_url=f"/openapi.json",
            docs_url=f"/docs",
            redoc_url=f"/redoc",
            lifespan=lifespan,
        )

    def _add_middleware(self):
        """Adds middleware to the application"""

        self._verify_app()

        self._app.add_middleware(SlowAPIMiddleware)
        self._app.add_middleware(CorrelationIdMiddleware, header_name="X-Request-ID")

        # FIXME: probably depends on service environment
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=(["*"]),
            allow_origin_regex=r"https://.*\.niagads\.org",
            allow_methods=["GET"],
        )

    def add_router(
        self,
        route: APIRouter,
        *,
        include_in_schema: bool = True,
        rate_limit_exempt: bool = False,
        **kwargs,
    ) -> None:
        """Register a router, optionally exempting its endpoints from rate limits.

        Additional arguments are passed to FastAPI's ``include_router``.
        """
        if self._app is None:
            raise RuntimeError("Application is not initialized.")

        if rate_limit_exempt:
            for endpoint_route in route.routes:
                if isinstance(endpoint_route, APIRoute):
                    self._limiter.exempt(endpoint_route.endpoint)
        self._app.include_router(
            route,
            include_in_schema=include_in_schema,
            responses=(
                {code: response for code, response in RESPONSES.items() if code != 429}
                if rate_limit_exempt
                else RESPONSES
            ),
            **kwargs,
        )

    def _add_exception_handlers(self):
        """Adds exception handlers to the application"""

        self._verify_app()
        self._app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        add_runtime_exception_handler(self._app)
        add_request_validation_exception_handler(self._app)
        add_system_exception_handler(self._app)
        add_database_exception_handler(self._app)
        add_not_implemented_exception_handler(self._app)

    def get_openapi_yaml(self) -> str:
        """Get YAML-formatted openapi specification.

        Converts the API openapi JSON specification to yaml format and returns the formatted yaml

        adapted from https://github.com/tiangolo/fastapi/issues/1140#issuecomment-659469034
        """
        self._verify_app()
        openapi_json = self._app.openapi()
        yaml_str = StringIO()
        yaml.dump(openapi_json, yaml_str, sort_keys=False)
        return yaml_str.getvalue()
