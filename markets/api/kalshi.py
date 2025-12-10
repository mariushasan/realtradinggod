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
