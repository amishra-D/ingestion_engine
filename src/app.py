import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from scalar_fastapi import add_scalar_reference

from src.features.Auth.Presentation.routes import router as AuthRouter
from src.features.Ingestion.Presentation.routes import router as IngestionRouter
from src.features.Tradebook.Presentation.routers import router as TradebookRouter
from src.ingestion_engine.engine import ingestion_engine
from src.shared.config.settings import get_settings
from src.shared.database.connection import db

from src.features.Tradebook.Domain.exceptions import TradebookException
from src.features.Tradebook.Presentation.exception_handlers import (
    tradebook_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.create_connection()
    ingestion_task = None
    settings = get_settings()
    if settings.AUTO_INGESTION:
        await ingestion_engine.initialize()
        ingestion_task = asyncio.create_task(
            ingestion_engine.start(interval_seconds=settings.INGESTION_INTERVAL)
        )
    yield
    ingestion_engine.stop()
    if ingestion_task and not ingestion_task.done():
        ingestion_task.cancel()
    await db.close_connection()


app = FastAPI(
    title="Ingestion Engine API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(AuthRouter)

app.add_exception_handler(
    TradebookException,
    tradebook_exception_handler,
)

add_scalar_reference(
    app,
    route="/documentation",
    title="Ingestion Engine API",
    openapi_url="/openapi.json",
)

app.include_router(TradebookRouter)
# app.include_router(IngestionRouter)


@app.get("/")
def root():
    return {"message": "Ingestion Engine API is running"}


@app.get("/health")
def status():
    return {"status": "healthy"}
