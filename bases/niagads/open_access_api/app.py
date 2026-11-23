import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from niagads.api.common.app.factory import AppFactory
from niagads.api.common.app.types import AppMetadata
from niagads.database.genomicsdb.intervals import fetch_bin_index_reference
from niagads.open_access_api.ask.telemetry import configure_telemetry
from niagads.open_access_api.ask.transport import router as AskRouter
from niagads.open_access_api.dependencies import OpenAccessEndpointContext
from niagads.open_access_api.routes.query import router as QueryRouter
from niagads.open_access_api.routes.records.gene import router as GeneRecordRouter
from niagads.open_access_api.routes.records.region import router as RegionRecordRouter
from niagads.open_access_api.routes.records.track import router as TrackRecordRouter
from niagads.open_access_api.routes.records.variant import router as VariantRecordRouter
from niagads.open_access_api.routes.service import router as ServiceRouter
from niagads.settings.core import ServiceEnvironment, get_service_environment

from pathlib import Path

description_md_path = Path(__file__).resolve().parent / "data" / "api_description.md"
description = description_md_path.read_text(encoding="utf-8")

metadata = AppMetadata(
    title="NIAGADS Open Access API",
    description=description,
    summary=(
        "NIAGADS Open Access API for Alzheimer's disease and related dementias "
        "genomic data and annotations."
    ),
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Initialize resources and close database and cache pools on shutdown."""
    logging.getLogger("uvicorn.error.niagads").setLevel(
        logging.DEBUG
        if get_service_environment() == ServiceEnvironment.DEV
        else logging.INFO
    )
    database_dependency = (
        OpenAccessEndpointContext.model_fields["database_session"]
        .metadata[0]
        .dependency
    )
    cache_dependency = (
        OpenAccessEndpointContext.model_fields["cache_manager"].metadata[0].dependency
    )
    try:
        await OpenAccessEndpointContext.verify_database_connection()
        async with database_dependency.session_ctx() as session:
            app.state.bin_index_reference = await fetch_bin_index_reference(session)
        yield
    finally:
        try:
            await database_dependency.close()
        finally:
            await cache_dependency.close()


# generate the app
app_factory = AppFactory(
    metadata=metadata,
    env=get_service_environment(),
    lifespan=lifespan,
)
app_factory.add_router(GeneRecordRouter)
app_factory.add_router(TrackRecordRouter)
app_factory.add_router(VariantRecordRouter)
app_factory.add_router(QueryRouter)
app_factory.add_router(RegionRecordRouter)
app_factory.add_router(ServiceRouter, rate_limit_exempt=True)
# app_factory.add_router(AskRouter, rate_limit_exempt=True)

# get the application object
app = app_factory.app

configure_telemetry(app)

if __name__ == "__main__":
    uvicorn.run(app="app:app")
