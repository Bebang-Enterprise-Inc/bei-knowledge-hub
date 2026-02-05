"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import config

# Import routers (will be created in later tasks)
# from .api import ingest, search, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"🚀 Starting {config.app_name} v{config.app_version}")
    print(f"Environment: {config.environment}")

    # Initialize observability (OpenTelemetry, Langfuse)
    # TODO: Task 14

    yield

    # Shutdown
    print(f"🛑 Shutting down {config.app_name}")


# Create FastAPI app
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="Vision-powered RAG system with Gemini 2.0 Flash",
    lifespan=lifespan,
    docs_url="/docs" if config.debug else None,
    redoc_url="/redoc" if config.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (will be added in later tasks)
# app.include_router(ingest.router, prefix="/api", tags=["ingest"])
# app.include_router(search.router, prefix="/api", tags=["search"])
# app.include_router(analytics.router, prefix="/api", tags=["analytics"])


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "name": config.app_name,
        "version": config.app_version,
        "status": "running",
        "docs": "/docs" if config.debug else "disabled"
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    # TODO: Add database connectivity check
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics() -> JSONResponse:
    """Prometheus metrics endpoint."""
    # TODO: Task 14 - Add OpenTelemetry metrics
    return JSONResponse(
        content={"message": "Metrics endpoint - to be implemented"},
        status_code=501
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level=config.log_level
    )
