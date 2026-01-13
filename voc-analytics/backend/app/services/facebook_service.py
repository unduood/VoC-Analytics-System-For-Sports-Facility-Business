"""
Facebook Graph API service for fetching comment and post details
"""
import httpx
import json
import logging
from typing import Dict, Any, Optional

from app.config import settings
from app.redis_client import redis_manager
from app.exceptions import FacebookGraphAPIError

logger = logging.getLogger(__name__)


class FacebookService:
    """Service for interacting with Facebook Graph API"""

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Facebook service

        Args:
            access_token: Facebook Page Access Token (optional, defaults to settings)

        Raises:
            ValueError: If no access token provided
        """
        self.access_token = access_token or settings.FACEBOOK_PAGE_ACCESS_TOKEN
        if not self.access_token:
            raise ValueError("Facebook Page Access Token is required")

        # Use configurable API version from settings
        self.base_url = f"https://graph.facebook.com/{settings.FACEBOOK_GRAPH_API_VERSION}"
        logger.info(f"FacebookService initialized with API version: {settings.FACEBOOK_GRAPH_API_VERSION}")


    async def get_post_details(self, post_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Fetch post details from Graph API with Redis caching

        Fetches post message and created_time. Results are cached in Redis
        to minimize API calls (multiple comments on same post).

        Args:
            post_id: Facebook post ID (format: {page-id}_{post-id})
            use_cache: Whether to use Redis cache (default: True)

        Returns:
            Dict containing:
                - id: str (post ID)
                - message: str (optional - may not exist)
                - created_time: str (ISO 8601)

        Raises:
            FacebookGraphAPIError: If API request fails
        """
        # Check cache first
        if use_cache:
            cache_key = f"fb_post:{post_id}"
            cached_data = await redis_manager.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for post {post_id}")
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid cached data for post {post_id}: {e}")
                    # Continue to fetch from API

        # Fetch from API
        fields = "message,created_time"
        url = f"{self.base_url}/{post_id}"
        params = {"fields": fields, "access_token": self.access_token}

        # Debug logging: show token prefix and URL for troubleshooting
        token_prefix = self.access_token[:20] if self.access_token else "None"
        logger.debug(f"Graph API request: {url}?fields={fields}&access_token={token_prefix}...")
        logger.debug(f"Token length: {len(self.access_token) if self.access_token else 0} characters")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            logger.info(f"Successfully fetched post details from Graph API: {post_id}")
            logger.debug(f"Post data: {data}")

            # Cache the result (1 hour expiration)
            if use_cache:
                cache_key = f"fb_post:{post_id}"
                cache_success = await redis_manager.set(
                    cache_key,
                    json.dumps(data),
                    expire=3600  # 1 hour
                )
                if cache_success:
                    logger.info(f"Cached post details: {post_id}")
                else:
                    logger.warning(f"Failed to cache post details: {post_id}")

            return data

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            logger.error(f"Graph API HTTP error fetching post {post_id}: {e.response.status_code} - {error_detail}")
            raise FacebookGraphAPIError(
                message=f"HTTP {e.response.status_code}: {error_detail}",
                details={"post_id": post_id}
            )

        except httpx.RequestError as e:
            logger.error(f"Graph API request error for post {post_id}: {e}")
            raise FacebookGraphAPIError(
                message=f"Request failed: {str(e)}",
                details={"post_id": post_id}
            )

        except Exception as e:
            logger.error(f"Unexpected error fetching post {post_id}: {e}", exc_info=True)
            raise FacebookGraphAPIError(
                message=f"Unexpected error: {str(e)}",
                details={"post_id": post_id}
            )

    async def invalidate_post_cache(self, post_id: str):
        """
        Invalidate cached post data

        Use this when post is edited or deleted on Facebook.

        Args:
            post_id: Facebook post ID
        """
        cache_key = f"fb_post:{post_id}"
        success = await redis_manager.delete(cache_key)
        if success:
            logger.info(f"Invalidated cache for post {post_id}")
        else:
            logger.warning(f"Failed to invalidate cache for post {post_id}")
