"""
Main FastAPI application
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.rabbitmq import rabbitmq_manager

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
        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")

        # Connect to RabbitMQ
        logger.info("Connecting to RabbitMQ...")
        rabbitmq_manager.connect()
        logger.info("RabbitMQ connected successfully")

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
