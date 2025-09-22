"""
Forenlytic Backend - Main FastAPI Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import os

from app.config import settings
from app.database import init_db
from app.api import auth, cases, reports
from app.utils.logging import setup_logging, log_startup_info, log_database_info, log_shutdown

# Setup logging
logger = setup_logging()

# Create upload directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.analysis_dir, exist_ok=True)
os.makedirs(settings.reports_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    log_startup_info(logger)
    init_db()
    log_database_info(logger)
    # log_server_ready(logger)
    
    yield
    
    # Shutdown
    log_shutdown(logger)


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="Comprehensive Digital Forensics Analysis Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)

# Include API routers
app.include_router(
    auth.router,
    prefix=f"{settings.api_v1_str}/auth",
    tags=["Authentication"]
)

app.include_router(
    cases.router,
    prefix=f"{settings.api_v1_str}/cases",
    tags=["Case Management"]
)

app.include_router(
    reports.router,
    prefix=f"{settings.api_v1_str}/reports",
    tags=["Report Generation"]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Forenlytic Backend",
        "version": settings.version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.version,
        "database": "connected"
    }


@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint to prevent 404 errors"""
    # Return a simple response instead of actual favicon file
    return {"message": "No favicon available"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
