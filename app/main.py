import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.filterwarnings('ignore', message='.*OLE2 inconsistency.*')
warnings.filterwarnings('ignore', message='.*file size.*not.*multiple of sector size.*')
warnings.filterwarnings('ignore', message='.*SSCS size is 0 but SSAT size is non-zero.*')
warnings.filterwarnings('ignore', message=r'.*WARNING \*\*\*.*')
warnings.filterwarnings('ignore', message='.*bcrypt.*')
warnings.filterwarnings('ignore', message='.*error reading bcrypt.*')

from fastapi import FastAPI, Request, HTTPException  # type: ignore
from fastapi.responses import JSONResponse, Response  # type: ignore
from contextlib import asynccontextmanager
import uvicorn  # type: ignore

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.health import router as health_router
from app.middleware.cors import add_cors_middleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.timeout import TimeoutMiddleware
from app.middleware.auth_middleware import AuthMiddleware
from app.api.v1 import (
    dashboard_routes,
    analytics_file_routes,
    analytics_sdp_routes,
    analytics_device_routes,
    analytics_management_routes,
    analytics_report_routes,
    analytics_contact_routes,
    analytics_apk_routes,
    analytics_communication_enhanced_routes,
    analytics_social_media_routes,
    auth_routes,
    case_routes,
    case_log_routes,
    case_note_routes,
    person_routes,
    evidence_routes,
    suspect_routes,
    report_routes
)
from fastapi.openapi.utils import get_openapi  # type: ignore
from app.db.init_db import init_db

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"API: {settings.API_V1_STR}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    try:
        init_db()
        logger.info("Database connected")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    logger.info("Server shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Digital Forensics Analysis Platform - Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

add_cors_middleware(app)

app.add_middleware(LoggingMiddleware)
app.add_middleware(TimeoutMiddleware, timeout_seconds=3600)
app.add_middleware(AuthMiddleware)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Masukkan token JWT kamu di sini. Contoh: `Bearer eyJhbGciOiJIUzI1Ni...`"
        }
    }

    openapi_schema["security"] = [{"BearerAuth": []}]

    public_paths = [
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/dashboard/landing",
        "/api/v1/file-encryptor/convert-to-sdp",
        "/api/v1/file-encryptor/list-sdp",
        "/api/v1/file-encryptor/download-sdp",
        "/api/v1/file-encryptor/progress/{upload_id}",
        '/health/health',
        '/health/health/ready',
        '/health/health/live',
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    ]

    for path, path_item in openapi_schema["paths"].items():
        if any(path.startswith(pub) for pub in public_paths):
            for method in path_item.values():
                method["security"] = []

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# app.include_router(dashboard_routes.router, prefix=settings.API_V1_STR, tags=["Dashboard"])
app.include_router(analytics_sdp_routes.router, prefix=settings.API_V1_STR, tags=["File Encryptor"])
app.include_router(auth_routes.router, prefix=settings.API_V1_STR, tags=["Auth"])
# app.include_router(case_routes.router, prefix=settings.API_V1_STR, tags=["Case Management"])
# app.include_router(case_log_routes.router, prefix=settings.API_V1_STR, tags=["Case Log Management"])
# app.include_router(case_note_routes.router, prefix=settings.API_V1_STR, tags=["Case Note Management"])
# app.include_router(person_routes.router, prefix=settings.API_V1_STR, tags=["Person Management"])
# app.include_router(evidence_routes.router, prefix=settings.API_V1_STR, tags=["Evidence Management"])
# app.include_router(suspect_routes.router, prefix=settings.API_V1_STR, tags=["Suspect Management"])
# app.include_router(report_routes.router, prefix=settings.API_V1_STR, tags=["Reports"])

# ANALYTICS MANAGEMENTS
app.include_router(analytics_report_routes.router, prefix=settings.API_V1_STR, tags=["Analytics Reports"])
app.include_router(analytics_file_routes.router, prefix=settings.API_V1_STR, tags=["File Management"])
app.include_router(analytics_management_routes.router, prefix=settings.API_V1_STR, tags=["Analytics Management"])
app.include_router(analytics_device_routes.router, prefix=settings.API_V1_STR, tags=["Device Management"])
app.include_router(analytics_contact_routes.router, prefix=settings.API_V1_STR, tags=["Contact Correlation"])
app.include_router(analytics_management_routes.hashfile_router, prefix=settings.API_V1_STR, tags=["Hashfile Analytics"])
app.include_router(analytics_social_media_routes.router, prefix=settings.API_V1_STR, tags=["Social Media Correlation"])
app.include_router(analytics_communication_enhanced_routes.router, prefix=settings.API_V1_STR, tags=["Deep Communication Analytics"])
app.include_router(analytics_apk_routes.router, prefix=settings.API_V1_STR, tags=["APK Analysis"])

app.include_router(health_router, prefix="/health", tags=["Health"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "status" in exc.detail and "message" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": exc.status_code,
                "message": exc.detail
            }
        )


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


@app.get("/")
async def root():
    return {
        "status": 200,
        "message": "Digital Forensics Analysis Platform API",
        "version": settings.VERSION
    }


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=False
    )
