from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging import setup_logging, log_startup_info, log_shutdown
from app.core.health import router as health_router
from app.middleware.cors import add_cors_middleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.timeout import TimeoutMiddleware
from app.api.v1 import case_routes, evidence_routes, suspect_routes, dashboard_routes, report_routes, analytics_routes
from app.db.init_db import init_db


# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Digital Forensics v1.0.0")
    print("API: /api/v1")
    print("Debug: True")
    
    # Initialize database
    try:
        init_db()
        print("Database connected")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    print("Server shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Digital Forensics Analysis Platform - Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
add_cors_middleware(app)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(TimeoutMiddleware, timeout_seconds=3600)

# Include routers
app.include_router(dashboard_routes.router, prefix=settings.API_V1_STR, tags=["Dashboard"])
app.include_router(analytics_routes.router, prefix=settings.API_V1_STR, tags=["Analytics"])
app.include_router(case_routes.router, prefix=settings.API_V1_STR, tags=["Case Management"])
app.include_router(evidence_routes.router, prefix=settings.API_V1_STR, tags=["Evidence Management"])
app.include_router(suspect_routes.router, prefix=settings.API_V1_STR, tags=["Suspect Management"])
app.include_router(report_routes.router, prefix=settings.API_V1_STR, tags=["Reports"])
app.include_router(health_router, prefix="/health", tags=["Health"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "message": "Internal server error",
            "error": str(exc)
        }
    )


# Root endpoint
@app.get("/")
async def root():
    return {
        "status": 200,
        "message": "Digital Forensics Analysis Platform API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
