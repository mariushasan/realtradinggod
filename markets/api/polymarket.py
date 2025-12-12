import time
import requests
import logging

logger = logging.getLogger(__name__)


class PolymarketClient:
    """Client for Polymarket Gamma API"""

    GAMMA_HOST = 'https://gamma-api.polymarket.com'
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def _gamma_request(self, path: str, params: dict = None) -> dict:
        """Make request to Gamma API (public market data) with retry logic"""
        url = self.GAMMA_HOST + path

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Gamma API attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))

        raise last_error

    def get_events(
        self,
        offset: int = 0,
        limit: int = 100,
        active: bool = True,
        end_date_min: str = None
    ) -> list:
        """Get events from Gamma API with optional filtering"""
        params = {
            'limit': limit,
            'offset': offset,
            'active': str(active).lower(),
            'closed': 'false',
            # Exclude unused data to reduce response size
            'related_tags': 'false',
            'include_chat': 'false',
            'include_template': 'false'
        }
        if end_date_min is not None:
            params['end_date_min'] = end_date_min

        return self._gamma_request('/events', params)
