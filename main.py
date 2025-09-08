"""
HeadStart FastAPI Application
Main application entry point with middleware and route configuration

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Main FastAPI application with authentication, content processing, and security
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn
from contextlib import asynccontextmanager

# Import services and middleware
from config.settings import get_settings
from services.database import init_db
from services.security import SecurityHeadersMiddleware, RateLimitMiddleware
from services.exceptions import HeadStartException

# Import API routers
from api.auth import router as auth_router
from api.content import router as content_router
from api.user import router as user_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting HeadStart application")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error("Application startup failed", error=str(e))
        raise
    finally:
        # Shutdown
        logger.info("Shutting down HeadStart application")

# Create FastAPI application
app = FastAPI(
    title="HeadStart API",
    description="AI-Powered Learning Recommendation Platform",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    calls=100,  # 100 requests
    period=60   # per minute
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Global exception handler
@app.exception_handler(HeadStartException)
async def headstart_exception_handler(request: Request, exc: HeadStartException):
    """Handle HeadStart custom exceptions"""
    logger.error(
        "HeadStart exception occurred",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "timestamp": structlog.processors.TimeStamper(fmt="iso")._stamper(),
                "path": request.url.path
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        "Unexpected exception occurred",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred" if not settings.DEBUG else str(exc),
                "timestamp": structlog.processors.TimeStamper(fmt="iso")._stamper(),
                "path": request.url.path
            }
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "HeadStart API",
        "version": "1.0.0",
        "timestamp": structlog.processors.TimeStamper(fmt="iso")._stamper()
    }

# API version endpoint
@app.get("/version")
async def get_version():
    """Get API version information"""
    return {
        "name": "HeadStart API",
        "version": "1.0.0",
        "description": "AI-Powered Learning Recommendation Platform",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG
    }

# Include API routers
app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    content_router,
    prefix="/api/content",
    tags=["Content Management"]
)

app.include_router(
    user_router,
    prefix="/api/user",
    tags=["User Management"]
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to HeadStart API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Documentation not available in production",
        "health": "/health"
    }

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG
    )

# Updated 2025-09-05: Complete FastAPI application with authentication, security, and content processing