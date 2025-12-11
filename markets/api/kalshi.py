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
    # Rate limit: 20 requests/second for reads. Use 60ms min interval (~16 req/sec) for safety margin
    MIN_REQUEST_INTERVAL = 0.06

    def __init__(self, api_key_id: str = None, private_key_pem: str = None):
        self.api_key_id = api_key_id or os.environ.get('KALSHI_API_KEY_ID', '').strip('"\'')
        private_key_str = private_key_pem or os.environ.get('KALSHI_PRIVATE_KEY', '')

        self.private_key = None
        self._last_request_time = 0.0  # For rate limiting
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

    def _rate_limit(self):
        """Enforce rate limiting between API requests"""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            sleep_time = self.MIN_REQUEST_INTERVAL - elapsed
            time.sleep(sleep_time)
        self._last_request_time = time.monotonic()

    def _request(self, method: str, path: str, params: dict = None) -> dict:
        """Make request to Kalshi API with retry logic and rate limiting"""
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
                # Enforce rate limiting before each request attempt
                self._rate_limit()
                response = requests.request(method, url, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Kalshi API attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))

        raise last_error

    def get_events(self, status: str = 'open', limit: int = 200, cursor: str = None, with_nested_markets: bool = True, series_ticker: str = None) -> dict:
        """Get events from Kalshi"""
        params = {
            'status': status,
            'limit': limit,
            'cursor': cursor,
            'with_nested_markets': str(with_nested_markets).lower(),
            'series_ticker': series_ticker
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

    def get_all_open_events(self, series_ticker: str = None) -> list:
        """Fetch all open events with pagination, optionally filtered by series ticker"""
        all_events = []
        cursor = None

        while True:
            response = self.get_events(
                status='open',
                cursor=cursor,
                with_nested_markets=True,
                series_ticker=series_ticker
            )
            events = response.get('events', [])
            all_events.extend(events)

            cursor = response.get('cursor')
            if not cursor or not events:
                break

        return all_events

    def get_tags_by_categories(self) -> dict:
        """Get all tags organized by categories"""
        return self._request('GET', '/search/tags_by_categories')

    def get_series(self, category: str = None, tags: str = None) -> dict:
        """Get series list, optionally filtered by category or tags"""
        params = {}
        if category:
            params['category'] = category
        if tags:
            params['tags'] = tags
        return self._request('GET', '/series', params if params else None)

    def get_all_series_for_categories(self, categories: list) -> list:
        """Get all series for a list of categories"""
        all_series = []
        seen_tickers = set()

        for category in categories:
            try:
                response = self.get_series(category=category)
                series_list = response.get('series', [])
                for series in series_list:
                    ticker = series.get('ticker', '')
                    if ticker and ticker not in seen_tickers:
                        all_series.append(series)
                        seen_tickers.add(ticker)
            except Exception as e:
                logger.warning(f"Failed to fetch series for category {category}: {e}")

        return all_series

    def get_markets_by_series(self, series_ticker: str, status: str = 'open') -> list:
        """Get all markets for a specific series"""
        all_markets = []
        cursor = None

        while True:
            params = {
                'series_ticker': series_ticker,
                'status': status,
                'limit': 200,
                'cursor': cursor
            }
            response = self._request('GET', '/markets', params)
            markets = response.get('markets', [])
            all_markets.extend(markets)

            cursor = response.get('cursor')
            if not cursor or not markets:
                break

        return all_markets
