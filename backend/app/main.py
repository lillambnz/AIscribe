"""Main FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api import encounters, stream, exports, auth, health, billing


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting AIscribe backend...")

    # Create database tables (in production, use Alembic)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    print("Shutting down AIscribe backend...")
    await engine.dispose()


app = FastAPI(
    title="AIscribe API",
    description="Medical AI Transcription Platform - Australian Compliance Ready",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(billing.router, prefix="/v1/billing", tags=["billing"])
app.include_router(encounters.router, prefix="/v1/encounters", tags=["encounters"])
app.include_router(stream.router, prefix="/v1", tags=["streaming"])
app.include_router(exports.router, prefix="/v1/exports", tags=["exports"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AIscribe API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "compliance": {
            "data_residency": "Australia" if settings.AU_DATA_RESIDENCY else "Configurable",
            "privacy_framework": "Australian Privacy Act 1988",
            "encryption": "AES-256 at rest, TLS 1.3 in transit",
        }
    }
