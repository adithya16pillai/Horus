from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.api.routes import webhook, scan, status


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()
    
    # Setup logging first
    setup_logging()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="API for scanning dependencies for security vulnerabilities",
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(webhook.router, prefix="/api")
    app.include_router(scan.router, prefix="/api")
    app.include_router(status.router, prefix="/api")
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
        logger.debug(f"Debug mode: {settings.DEBUG}")
    
    return app


app = create_application()


# Root endpoint for health checks
@app.get("/")
async def root():
    settings = get_settings()
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "ok",
    }


if __name__ == "__main__":
    # Use this for local development
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )