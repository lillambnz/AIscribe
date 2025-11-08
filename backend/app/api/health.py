"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db

router = APIRouter()


@router.get("")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "service": "AIscribe API",
        "version": "0.1.0"
    }


@router.get("/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """Health check with database connectivity."""
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
