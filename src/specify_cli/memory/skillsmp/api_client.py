"""
SkillsMP API client for skill search.

Provides access to 425K+ agent skills from SkillsMP.com.
API Documentation: https://skillsmp.com/docs/api
"""

import requests
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

from ..logging import get_logger


class SkillsMPAPIClient:
    """Client for SkillsMP API."""

    # API endpoints (based on https://skillsmp.com/docs/api)
    BASE_URL = "https://skillsmp.com/api/v1"
    SEARCH_ENDPOINT = "/skills/search"
    AI_SEARCH_ENDPOINT = "/skills/ai-search"

    # Rate limiting
    DAILY_RATE_LIMIT = 500  # requests per day
    MAX_ITEMS_PER_PAGE = 100

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None
    ):
        """Initialize SkillsMP API client.

        Args:
            api_key: SkillsMP API key (format: sk_live_*)
            cache_dir: Directory for cache storage
        """
        self.logger = get_logger()
        self.api_key = api_key
        self.cache_dir = cache_dir or Path.home() / ".claude" / "memory" / "cache" / "skillsmp"

        # Session for connection pooling
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "SpecKit-Memory-System/1.0"
            })

        # Setup cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Track rate limit from headers
        self.daily_limit = self.DAILY_RATE_LIMIT
        self.daily_remaining = None
        self.limit_reset_time = None

    def _check_rate_limit(self) -> bool:
        """Check if we can make a request based on rate limit info.

        Returns:
            True if request allowed
        """
        if self.daily_remaining is not None and self.daily_remaining <= 0:
            # Check if reset time passed
            if self.limit_reset_time and datetime.now() >= self.limit_reset_time:
                self.daily_remaining = self.daily_limit
                self.limit_reset_time = None
            else:
                return False

        return True

    def _update_rate_limit_from_headers(self, headers: Dict[str, str]) -> None:
        """Update rate limit info from response headers.

        Args:
            headers: Response headers
        """
        try:
            daily_limit = headers.get("X-RateLimit-Daily-Limit")
            daily_remaining = headers.get("X-RateLimit-Daily-Remaining")

            if daily_limit:
                self.daily_limit = int(daily_limit)

            if daily_remaining:
                self.daily_remaining = int(daily_remaining)
        except (ValueError, TypeError):
            pass

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make authenticated API request.

        Args:
            endpoint: API endpoint (without /api/v1 prefix)
            params: Query parameters

        Returns:
            Response data or None
        """
        # Check rate limit
        if not self._check_rate_limit():
            self.logger.warning("Daily rate limit exceeded")
            return None

        if not self.api_key:
            self.logger.error("No API key configured")
            return None

        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=30
            )

            # Update rate limit from headers
            self._update_rate_limit_from_headers(response.headers)

            # Check response
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                error_data = response.json().get("error", {})
                error_code = error_data.get("code", "")

                if error_code == "MISSING_API_KEY":
                    self.logger.error("API key not provided")
                elif error_code == "INVALID_API_KEY":
                    self.logger.error("Invalid API key format")
                return None
            elif response.status_code == 429:
                self.logger.error("Daily quota exceeded")
                return None
            elif response.status_code == 400:
                error_data = response.json().get("error", {})
                self.logger.error(f"Bad request: {error_data.get('message', 'Unknown error')}")
                return None
            else:
                self.logger.warning(f"API error: {response.status_code}")
                return None

        except requests.Timeout:
            self.logger.warning("Request timeout")
            return None
        except Exception as e:
            self.logger.warning(f"Request error: {e}")
            return None

    def search_skills(
        self,
        query: str,
        limit: int = 10,
        page: int = 1,
        sort_by: str = "stars"
    ) -> List[Dict[str, Any]]:
        """Keyword search for skills.

        Args:
            query: Search query
            limit: Max results (max 100)
            page: Page number (default: 1)
            sort_by: Sort by "stars" or "recent"

        Returns:
            List of skill entries
        """
        # Check cache first
        cache_key = self._get_cache_key("search", query, page, sort_by)
        cached = self._get_cache(cache_key)
        if cached:
            self.logger.debug(f"Cache hit for search: {query}")
            return cached[:limit]

        # Validate parameters
        limit = min(limit, self.MAX_ITEMS_PER_PAGE)

        # Make API request
        params = {
            "q": query,
            "limit": limit,
            "page": page,
            "sortBy": sort_by
        }

        response = self._make_request(self.SEARCH_ENDPOINT, params=params)

        if not response:
            return []

        skills = response.get("skills", [])

        # Cache results (shorter TTL for keyword search)
        self._set_cache(cache_key, skills, ttl=1800)  # 30 min

        return skills

    def ai_search_skills(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """AI semantic search for skills.

        Args:
            query: Natural language search query
            limit: Max results

        Returns:
            List of relevant skills
        """
        # AI search results usually more relevant, cache longer
        cache_key = f"ai_search:{hashlib.md5(query.encode()).hexdigest()}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached[:limit]

        params = {
            "q": query,
            "limit": limit
        }

        response = self._make_request(self.AI_SEARCH_ENDPOINT, params=params)

        if not response:
            return []

        skills = response.get("skills", [])

        # Cache AI search results longer (more expensive)
        self._set_cache(cache_key, skills, ttl=7200)  # 2 hours

        return skills

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get skill details by ID.

        Args:
            skill_id: Skill identifier

        Returns:
            Skill details or None
        """
        # Check cache
        cache_key = f"skill:{skill_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        # Note: API doesn't specify a get-by-id endpoint in the docs
        # Would need to search and filter by ID
        self.logger.warning(f"Get by ID not supported, searching for: {skill_id}")

        # As fallback, try searching
        results = self.search_skills(skill_id, limit=1)

        if results and len(results) > 0:
            return results[0]

        return None

    def _get_cache_key(self, *args) -> str:
        """Generate cache key from arguments.

        Args:
            *args: Arguments to include in key

        Returns:
            Cache key string
        """
        key_str = ":".join(str(a) for a in args)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            import json
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check expiration
            expires_at = data.get("expires_at")
            if expires_at:
                exp_time = datetime.fromisoformat(expires_at)
                if datetime.now() > exp_time:
                    cache_file.unlink()
                    return None

            return data.get("value")

        except Exception:
            return None

    def _set_cache(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        cache_file = self.cache_dir / f"{key}.json"

        try:
            import json
            expires_at = datetime.now() + timedelta(seconds=ttl)

            data = {
                "value": value,
                "expires_at": expires_at.isoformat()
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)

        except Exception as e:
            self.logger.warning(f"Cache write error: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get API client status.

        Returns:
            Status dict
        """
        return {
            "api_key_configured": bool(self.api_key),
            "api_key_format": "sk_live_*" if self.api_key and self.api_key.startswith("sk_live_") else "invalid",
            "cache_dir": str(self.cache_dir),
            "daily_limit": self.daily_limit,
            "daily_remaining": self.daily_remaining,
            "limit_reset_time": self.limit_reset_time.isoformat() if self.limit_reset_time else None
        }


class SkillsMPError(Exception):
    """SkillsMP API error."""

    def __init__(self, message: str, code: Optional[str] = None):
        """Initialize error.

        Args:
            message: Error message
            code: Error code from API
        """
        super().__init__(message)
        self.code = code
