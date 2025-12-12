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
    MAX_RETRIES = 5
    RETRY_DELAY = 1
    # Adaptive rate limiting settings
    BASE_REQUEST_INTERVAL = 0.1  # Start with 100ms between requests
    MAX_REQUEST_INTERVAL = 2.0   # Cap at 2 seconds
    BACKOFF_MULTIPLIER = 2.0     # Double interval on 429
    RECOVERY_FACTOR = 0.95       # Slowly decrease interval on success

    def __init__(self, api_key_id: str = None, private_key_pem: str = None):
        self.api_key_id = api_key_id or os.environ.get('KALSHI_API_KEY_ID', '').strip('"\'')
        private_key_str = private_key_pem or os.environ.get('KALSHI_PRIVATE_KEY', '')

        self.private_key = None
        self._last_request_time = 0.0
        self._current_interval = self.BASE_REQUEST_INTERVAL
        if private_key_str and len(private_key_str) > 100:
            try:
                private_key_str = private_key_str.strip('"\'')
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
        """Enforce adaptive rate limiting between API requests"""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self._current_interval:
            time.sleep(self._current_interval - elapsed)
        self._last_request_time = time.monotonic()

    def _backoff(self):
        """Increase rate limit interval after hitting 429"""
        old_interval = self._current_interval
        self._current_interval = min(
            self._current_interval * self.BACKOFF_MULTIPLIER,
            self.MAX_REQUEST_INTERVAL
        )
        logger.info(f"Rate limit hit, increasing interval: {old_interval:.3f}s -> {self._current_interval:.3f}s")

    def _recover(self):
        """Slowly decrease rate limit interval after successful requests"""
        if self._current_interval > self.BASE_REQUEST_INTERVAL:
            self._current_interval = max(
                self._current_interval * self.RECOVERY_FACTOR,
                self.BASE_REQUEST_INTERVAL
            )

    def _request(self, method: str, path: str, params: dict = None) -> dict:
        """Make request to Kalshi API with retry logic and adaptive rate limiting"""
        url = self.BASE_URL + path

        if params:
            query_parts = [f"{k}={v}" for k, v in params.items() if v is not None]
            if query_parts:
                path = path + '?' + '&'.join(query_parts)
                url = self.BASE_URL + path

        headers = self._get_headers(method, path)

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                self._rate_limit()
                response = requests.request(method, url, headers=headers, timeout=30)

                if response.status_code == 429:
                    self._backoff()
                    retry_after = response.headers.get('Retry-After')
                    wait_time = float(retry_after) if retry_after else self._current_interval * (attempt + 1)
                    logger.warning(f"Kalshi API rate limited (429), waiting {wait_time:.2f}s before retry")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                self._recover()
                return response.json()
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Kalshi API attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))

        raise last_error

    def get_events(
        self,
        status: str = 'open',
        limit: int = 200,
        cursor: str = None,
        with_nested_markets: bool = True,
        series_ticker: str = None,
        min_close_ts: int = None,
        max_close_ts: int = None
    ) -> dict:
        """Get events from Kalshi with optional filtering"""
        params = {
            'status': status,
            'limit': limit,
            'cursor': cursor,
            'with_nested_markets': str(with_nested_markets).lower(),
            'series_ticker': series_ticker,
            'min_close_ts': min_close_ts,
            'max_close_ts': max_close_ts
        }
        return self._request('GET', '/events', params)

    def get_multivariate_events(
        self,
        limit: int = 200,
        cursor: str = None,
        with_nested_markets: bool = True,
        series_ticker: str = None,
        collection_ticker: str = None
    ) -> dict:
        """Get multivariate events (events with multiple outcome markets)"""
        params = {
            'limit': limit,
            'cursor': cursor,
            'with_nested_markets': str(with_nested_markets).lower(),
            'series_ticker': series_ticker,
            'collection_ticker': collection_ticker
        }
        return self._request('GET', '/events/multivariate', params)
