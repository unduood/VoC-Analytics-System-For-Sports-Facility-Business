"""
API v1 Router - Combines all v1 endpoints
"""
from fastapi import APIRouter

from app.api.v1.endpoints import webhooks, feedback, google_maps, analytics, analysis_correction

# Create main v1 router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(webhooks.router)
api_router.include_router(feedback.router)
api_router.include_router(google_maps.router)
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(analysis_correction.router)
