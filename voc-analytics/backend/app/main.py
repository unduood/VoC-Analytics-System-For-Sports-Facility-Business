"""
Main FastAPI application
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, close_db
from app.rabbitmq import rabbitmq_manager
from app.redis_client import redis_manager
from app.api.v1.router import api_router
from app.exceptions import VoCAnalyticsException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown events
    """
    # Startup
    logger.info("Starting up VoC Analytics Backend...")

    try:
        # Validate Facebook webhook configuration
        logger.info("Validating Facebook webhook configuration...")
        if not settings.FACEBOOK_APP_SECRET:
            logger.warning(
                "FACEBOOK_APP_SECRET not configured. "
                "Facebook webhooks will not work without this setting."
            )
        else:
            logger.info("Facebook webhook signature validation enabled")

        if not settings.FACEBOOK_PAGE_ACCESS_TOKEN:
            logger.warning(
                "FACEBOOK_PAGE_ACCESS_TOKEN not configured. "
                "Facebook Graph API calls will fail."
            )
        else:
            logger.info("Facebook Graph API access configured")

        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")

        # Connect to RabbitMQ
        logger.info("Connecting to RabbitMQ...")
        rabbitmq_manager.connect()
        logger.info("RabbitMQ connected successfully")

        # Connect to Redis
        logger.info("Connecting to Redis...")
        await redis_manager.connect()
        logger.info("Redis connected successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down VoC Analytics Backend...")

    try:
        # Close RabbitMQ connection
        rabbitmq_manager.close()
        logger.info("RabbitMQ connection closed")

        # Close Redis connection
        await redis_manager.disconnect()
        logger.info("Redis connection closed")

        # Close database connection
        await close_db()
        logger.info("Database connection closed")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Voice of Customer Analytics System - Backend API",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(VoCAnalyticsException)
async def voc_exception_handler(request: Request, exc: VoCAnalyticsException):
    """Handle custom VoC Analytics exceptions"""
    logger.error(f"VoCAnalyticsException: {exc.message}", extra=exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "details": {"message": str(exc)} if settings.DEBUG else {}
        }
    )


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint

    Returns service status and dependencies
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint

    Returns welcome message and API information
    """
    return {
        "message": "Welcome to VoC Analytics System",
        "version": "0.1.0",
        "docs_url": "/docs",
        "health_check": "/health"
    }


# Example endpoint to publish message to RabbitMQ
@app.post("/api/test/publish", tags=["Testing"])
async def test_publish_message(message: dict):
    """
    Test endpoint to publish a message to RabbitMQ

    This is for testing purposes only
    """
    success = rabbitmq_manager.publish_message(
        queue_name="data_ingestion",
        message=message
    )

    if success:
        return {
            "status": "success",
            "message": "Message published to queue",
            "data": message
        }
    else:
        return {
            "status": "error",
            "message": "Failed to publish message"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
