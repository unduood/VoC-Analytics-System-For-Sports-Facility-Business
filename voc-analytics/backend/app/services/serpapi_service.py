"""
SerpAPI service for fetching Google Maps reviews
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class SerpAPIError(Exception):
    """Custom exception for SerpAPI-related errors"""
    pass


class SerpAPIService:
    """Service for interacting with SerpAPI Google Maps Reviews"""

    BASE_URL = "https://serpapi.com/search"

    def __init__(self, api_key: str):
        """
        Initialize SerpAPI service

        Args:
            api_key: SerpAPI authentication key
        """
        self.api_key = api_key

    async def fetch_google_maps_reviews(
        self,
        data_id: str,
        max_reviews: int = 20,
        hl: str = "th"
    ) -> List[Dict[str, Any]]:
        """
        Fetch Google Maps reviews from SerpAPI with pagination

        Reviews are fetched in newest-first order (sort_by="newestFirst")
        to ensure we get the latest reviews from the location.

        Note:
        - SerpAPI returns 8 reviews on the first page by default
        - Uses no_cache=true to always fetch fresh data from Google Maps
        - This ensures edited reviews are detected immediately

        Args:
            data_id: Google Maps place data ID
            max_reviews: Maximum number of reviews to fetch (default: 20)
            hl: Language code (default: "th" for Thai)

        Returns:
            List of review dictionaries (up to max_reviews), sorted newest first

        Raises:
            SerpAPIError: If API call fails or returns error
        """
        all_reviews = []
        next_page_token = None
        page_count = 0
        max_pages = 3  # Limit to prevent infinite loops (8 + 10 + 10 = 28 reviews max)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Fetching Google Maps reviews for data_id: {data_id} (target: {max_reviews} reviews)")

                while len(all_reviews) < max_reviews and page_count < max_pages:
                    page_count += 1

                    # Build params for this page
                    params = {
                        "engine": "google_maps_reviews",
                        "data_id": data_id,
                        "api_key": self.api_key,
                        "hl": hl,
                        "sort_by": "newestFirst",  # Fetch latest reviews first
                        "no_cache": "true"  # Always fetch fresh data to detect edited reviews
                    }

                    # Add next_page_token if this is not the first page
                    if next_page_token:
                        params["next_page_token"] = next_page_token
                        logger.info(f"Fetching page {page_count} with next_page_token")
                    else:
                        logger.info(f"Fetching page {page_count} (initial page)")

                    # Make request
                    response = await client.get(self.BASE_URL, params=params)
                    response.raise_for_status()

                    data = response.json()

                    # Check for SerpAPI error in response
                    if "error" in data:
                        raise SerpAPIError(f"SerpAPI error: {data['error']}")

                    # Get reviews from this page
                    page_reviews = data.get("reviews", [])
                    logger.info(f"Page {page_count} returned {len(page_reviews)} reviews")

                    if not page_reviews:
                        logger.info("No more reviews available")
                        break

                    # Add reviews to collection
                    all_reviews.extend(page_reviews)

                    # Check if there's a next page
                    pagination = data.get("serpapi_pagination", {})
                    next_page_token = pagination.get("next_page_token")

                    if not next_page_token:
                        logger.info("No next_page_token found, stopping pagination")
                        break

                # Trim to max_reviews if we fetched more
                if len(all_reviews) > max_reviews:
                    logger.info(f"Trimming {len(all_reviews)} reviews to {max_reviews}")
                    all_reviews = all_reviews[:max_reviews]

                logger.info(f"Successfully fetched {len(all_reviews)} reviews from SerpAPI across {page_count} page(s)")

                return all_reviews

        except httpx.TimeoutException as e:
            logger.error(f"SerpAPI request timeout: {e}")
            raise SerpAPIError("Request to SerpAPI timed out")

        except httpx.HTTPStatusError as e:
            logger.error(f"SerpAPI HTTP error: {e}")
            raise SerpAPIError(f"HTTP error from SerpAPI: {e.response.status_code}")

        except httpx.RequestError as e:
            logger.error(f"SerpAPI request error: {e}")
            raise SerpAPIError(f"Failed to connect to SerpAPI: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error fetching reviews: {e}", exc_info=True)
            raise SerpAPIError(f"Unexpected error: {str(e)}")

    @staticmethod
    def parse_review_to_feedback_data(review: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse SerpAPI review into feedback record data

        Args:
            review: Raw review dictionary from SerpAPI

        Returns:
            Dictionary with keys:
                - source_id: review_id
                - text_content: Thai review snippet
                - raw_data: Structured review data
                - created_at_source: Last edit timestamp
            Returns None if required fields are missing
        """
        try:
            # Extract required fields
            review_id = review.get("review_id")
            snippet = review.get("snippet", "")

            if not review_id:
                logger.warning("Review missing review_id, skipping")
                return None

            if not snippet or not snippet.strip():
                logger.info(f"Review {review_id} is rating-only (no text content), skipping")
                return None

            # Extract optional fields with defaults
            extracted_snippet = review.get("extracted_snippet", {})
            user = review.get("user", {})
            rating = review.get("rating")
            iso_date = review.get("iso_date")
            iso_date_of_last_edit = review.get("iso_date_of_last_edit")

            # Parse timestamps
            created_at_source = None
            if iso_date_of_last_edit:
                try:
                    created_at_source = datetime.fromisoformat(
                        iso_date_of_last_edit.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError) as e:
                    logger.warning(
                        f"Invalid iso_date_of_last_edit format: {iso_date_of_last_edit}, error: {e}"
                    )

            # If no last edit date, try original date
            if not created_at_source and iso_date:
                try:
                    created_at_source = datetime.fromisoformat(
                        iso_date.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Invalid iso_date format: {iso_date}, error: {e}")

            # Build raw_data structure as specified in requirements
            raw_data = {
                "review_id": review_id,
                "snippet": snippet,
                "original": extracted_snippet.get("original", snippet),
                "link": review.get("link"),
                "rating": rating,
                "iso_date": iso_date,
                "iso_date_of_last_edit": iso_date_of_last_edit,
                "name": user.get("name")
            }

            return {
                "source_id": review_id,
                "text_content": snippet,  # Thai text for NLP models
                "raw_data": raw_data,
                "created_at_source": created_at_source
            }

        except Exception as e:
            logger.error(f"Error parsing review: {e}", exc_info=True)
            return None
