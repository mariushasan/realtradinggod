import os
import base64
import datetime
import time
import requests
import logging
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)


class KalshiClient:
    """Client for Kalshi API"""

    BASE_URL = 'https://api.elections.kalshi.com/trade-api/v2'
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self, api_key_id: str = None, private_key_pem: str = None):
        self.api_key_id = api_key_id or os.environ.get('KALSHI_API_KEY_ID', '').strip('"\'')
        private_key_str = private_key_pem or os.environ.get('KALSHI_PRIVATE_KEY', '')

        self.private_key = None
        if private_key_str and len(private_key_str) > 100:  # Valid key should be much longer
            try:
                # Strip quotes if present
                private_key_str = private_key_str.strip('"\'')
                # Handle escaped newlines
                private_key_str = private_key_str.replace('\\n', '\n')
                self.private_key = serialization.load_pem_private_key(
                    private_key_str.encode('utf-8'),
                    password=None,
                    backend=default_backend()
                )
            except Exception as e:
                logger.warning(f"Could not load Kalshi private key: {e}")

    def _create_signature(self, timestamp: str, method: str, path: str) -> str:
        """Create RSA-PSS signature for request"""
        if not self.private_key:
            return ''

        path_without_query = path.split('?')[0]
        message = f"{timestamp}{method}{path_without_query}".encode('utf-8')
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')

    def _get_headers(self, method: str, path: str) -> dict:
        """Get headers for request (authenticated if possible)"""
        headers = {'Content-Type': 'application/json'}

        if self.private_key and self.api_key_id:
            timestamp = str(int(datetime.datetime.now().timestamp() * 1000))
            signature = self._create_signature(timestamp, method, path)
            headers.update({
                'KALSHI-ACCESS-KEY': self.api_key_id,
                'KALSHI-ACCESS-SIGNATURE': signature,
                'KALSHI-ACCESS-TIMESTAMP': timestamp,
            })

        return headers

    def _request(self, method: str, path: str, params: dict = None) -> dict:
        """Make request to Kalshi API with retry logic"""
        url = self.BASE_URL + path

        if params:
            # Build query string
            query_parts = []
            for k, v in params.items():
                if v is not None:
                    query_parts.append(f"{k}={v}")
            if query_parts:
                path = path + '?' + '&'.join(query_parts)
                url = self.BASE_URL + path

        headers = self._get_headers(method, path)

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.request(method, url, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Kalshi API attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))

        raise last_error

    def get_events(self, status: str = 'open', limit: int = 200, cursor: str = None, with_nested_markets: bool = True) -> dict:
        """Get events from Kalshi"""
        params = {
            'status': status,
            'limit': limit,
            'cursor': cursor,
            'with_nested_markets': str(with_nested_markets).lower()
        }
        return self._request('GET', '/events', params)

    def get_event(self, event_ticker: str, with_nested_markets: bool = True) -> dict:
        """Get single event by ticker"""
        params = {'with_nested_markets': str(with_nested_markets).lower()}
        return self._request('GET', f'/events/{event_ticker}', params)

    def get_markets(self, status: str = 'open', limit: int = 200, cursor: str = None, event_ticker: str = None) -> dict:
        """Get markets from Kalshi"""
        params = {
            'status': status,
            'limit': limit,
            'cursor': cursor,
            'event_ticker': event_ticker
        }
        return self._request('GET', '/markets', params)

    def get_market(self, ticker: str) -> dict:
        """Get single market by ticker"""
        return self._request('GET', f'/markets/{ticker}')

    def get_all_open_markets(self) -> list:
        """Fetch all open markets with pagination"""
        all_markets = []
        cursor = None

        while True:
            response = self.get_markets(status='open', cursor=cursor)
            markets = response.get('markets', [])
            all_markets.extend(markets)

            cursor = response.get('cursor')
            if not cursor or not markets:
                break

        return all_markets

    def get_all_open_events(self) -> list:
        """Fetch all open events with pagination"""
        all_events = []
        cursor = None

        while True:
            response = self.get_events(status='open', cursor=cursor, with_nested_markets=True)
            events = response.get('events', [])
            all_events.extend(events)

            cursor = response.get('cursor')
            if not cursor or not events:
                break

        return all_events

    def get_tags_by_categories(self) -> dict:
        """Get all tags organized by categories"""
        response = self._request('GET', '/search/tags_by_categories')
        return response.get('tags_by_categories', {})

    def get_series(self, series_ticker: str, include_product_metadata: bool = False) -> dict:
        """Get a single series by ticker"""
        params = {'include_product_metadata': str(include_product_metadata).lower()}
        return self._request('GET', f'/series/{series_ticker}', params)

    def get_series_list(self, category: str = None, tags: str = None, include_product_metadata: bool = False) -> list:
        """
        Get list of series with optional filtering by category or tags.

        Args:
            category: Filter by category (e.g., 'Politics', 'Economics', 'Sports')
            tags: Filter by tags (comma-separated, e.g., 'fed,inflation')
            include_product_metadata: Include additional product metadata

        Returns:
            List of series objects
        """
        params = {
            'category': category,
            'tags': tags,
            'include_product_metadata': str(include_product_metadata).lower()
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        response = self._request('GET', '/series', params if params else None)
        return response.get('series', [])

    def get_markets_by_series(self, series_ticker: str, status: str = 'open', limit: int = 200, cursor: str = None) -> dict:
        """Get markets filtered by series ticker"""
        params = {
            'series_ticker': series_ticker,
            'status': status,
            'limit': limit,
            'cursor': cursor
        }
        return self._request('GET', '/markets', params)

    def get_all_markets_by_series(self, series_ticker: str, status: str = 'open') -> list:
        """Fetch all markets for a series with pagination"""
        all_markets = []
        cursor = None

        while True:
            response = self.get_markets_by_series(series_ticker, status=status, cursor=cursor)
            markets = response.get('markets', [])
            all_markets.extend(markets)

            cursor = response.get('cursor')
            if not cursor or not markets:
                break

        return all_markets

    def get_markets_by_category(self, category: str = None, tags: str = None, status: str = 'open') -> list:
        """
        Get markets filtered by category/tags using a two-step process:
        1. Fetch series matching the category/tags
        2. Fetch markets for those series

        Args:
            category: Filter by category (e.g., 'Politics', 'Economics')
            tags: Filter by tags (comma-separated)
            status: Market status filter

        Returns:
            List of market objects
        """
        # Step 1: Get series matching the category/tags
        series_list = self.get_series_list(category=category, tags=tags)

        if not series_list:
            logger.info(f"No series found for category={category}, tags={tags}")
            return []

        # Step 2: Fetch markets for each series
        all_markets = []
        for series in series_list:
            series_ticker = series.get('ticker')
            if series_ticker:
                markets = self.get_all_markets_by_series(series_ticker, status=status)
                # Add series metadata to each market for reference
                for market in markets:
                    market['_series_category'] = series.get('category')
                    market['_series_tags'] = series.get('tags', [])
                all_markets.extend(markets)

        logger.info(f"Found {len(all_markets)} markets for category={category}, tags={tags} across {len(series_list)} series")
        return all_markets

    def get_events_by_series(self, series_ticker: str, status: str = 'open', limit: int = 200, cursor: str = None, with_nested_markets: bool = True) -> dict:
        """Get events filtered by series ticker"""
        params = {
            'series_ticker': series_ticker,
            'status': status,
            'limit': limit,
            'cursor': cursor,
            'with_nested_markets': str(with_nested_markets).lower()
        }
        return self._request('GET', '/events', params)

    def get_all_events_by_series(self, series_ticker: str, status: str = 'open', with_nested_markets: bool = True) -> list:
        """Fetch all events for a series with pagination"""
        all_events = []
        cursor = None

        while True:
            response = self.get_events_by_series(series_ticker, status=status, cursor=cursor, with_nested_markets=with_nested_markets)
            events = response.get('events', [])
            all_events.extend(events)

            cursor = response.get('cursor')
            if not cursor or not events:
                break

        return all_events

    def get_events_by_category(self, category: str = None, tags: str = None, status: str = 'open', with_nested_markets: bool = True) -> list:
        """
        Get events filtered by category/tags using a two-step process:
        1. Fetch series matching the category/tags
        2. Fetch events for those series

        Args:
            category: Filter by category (e.g., 'Politics', 'Economics')
            tags: Filter by tags (comma-separated)
            status: Event status filter
            with_nested_markets: Include nested markets in response

        Returns:
            List of event objects with their markets
        """
        # Step 1: Get series matching the category/tags
        series_list = self.get_series_list(category=category, tags=tags)

        if not series_list:
            logger.info(f"No series found for category={category}, tags={tags}")
            return []

        # Step 2: Fetch events for each series
        all_events = []
        for series in series_list:
            series_ticker = series.get('ticker')
            if series_ticker:
                events = self.get_all_events_by_series(series_ticker, status=status, with_nested_markets=with_nested_markets)
                # Add series metadata to each event for reference
                for event in events:
                    event['_series_category'] = series.get('category')
                    event['_series_tags'] = series.get('tags', [])
                all_events.extend(events)

        logger.info(f"Found {len(all_events)} events for category={category}, tags={tags} across {len(series_list)} series")
        return all_events
