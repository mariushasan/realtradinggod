import os
import time
import hmac
import hashlib
import base64
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PolymarketClient:
    """Client for Polymarket CLOB API"""

    CLOB_HOST = 'https://clob.polymarket.com'
    GAMMA_HOST = 'https://gamma-api.polymarket.com'
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        passphrase: str = None
    ):
        self.api_key = api_key or os.environ.get('POLYMARKET_API_KEY', '').strip('"\'')
        self.api_secret = api_secret or os.environ.get('POLYMARKET_API_SECRET', '').strip('"\'')
        self.passphrase = passphrase or os.environ.get('POLYMARKET_PASSPHRASE', '').strip('"\'')

    def _get_l2_headers(self, method: str, path: str, body: str = '') -> dict:
        """Generate L2 authentication headers using HMAC-SHA256"""
        timestamp = str(int(time.time()))

        # Create signature
        message = f"{timestamp}{method}{path}{body}"
        try:
            signature = base64.b64encode(
                hmac.new(
                    base64.b64decode(self.api_secret),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')
        except Exception:
            signature = ''

        return {
            'POLY-ADDRESS': os.environ.get('POLYMARKET_WALLET_ADDRESS', '').strip('"\''),
            'POLY-SIGNATURE': signature,
            'POLY-TIMESTAMP': timestamp,
            'POLY-API-KEY': self.api_key,
            'POLY-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }

    def _clob_request(self, method: str, path: str, params: dict = None, authenticated: bool = False) -> dict:
        """Make request to CLOB API with retry logic"""
        url = self.CLOB_HOST + path

        headers = {'Content-Type': 'application/json'}
        if authenticated and self.api_key:
            headers = self._get_l2_headers(method, path)

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                if method == 'GET' and params:
                    response = requests.get(url, params=params, headers=headers, timeout=30)
                else:
                    response = requests.request(method, url, headers=headers, timeout=30)

                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"CLOB API attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))

        raise last_error

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

    def get_markets(self, offset: int = 0, limit: int = 100, active: bool = True, tag_id: int = None) -> list:
        """Get markets from Gamma API"""
        params = {
            'limit': limit,
            'offset': offset,
            'active': str(active).lower(),
            'closed': 'false'
        }
        if tag_id is not None:
            params['tag_id'] = tag_id
        return self._gamma_request('/markets', params)

    def get_market(self, condition_id: str) -> dict:
        """Get single market by condition ID from Gamma API"""
        return self._gamma_request(f'/markets/{condition_id}')

    def get_events(self, offset: int = 0, limit: int = 100, active: bool = True) -> list:
        """Get events from Gamma API"""
        params = {
            'limit': limit,
            'offset': offset,
            'active': str(active).lower(),
            'closed': 'false'
        }
        return self._gamma_request('/events', params)

    def get_event(self, event_slug: str) -> dict:
        """Get single event by slug from Gamma API"""
        return self._gamma_request(f'/events/{event_slug}')

    def get_prices(self, token_ids: list) -> dict:
        """Get current prices for tokens from CLOB API"""
        # Prices endpoint accepts comma-separated token IDs
        params = {'token_ids': ','.join(token_ids)}
        return self._clob_request('GET', '/prices', params)

    def get_midpoint(self, token_id: str) -> Optional[float]:
        """Get midpoint price for a token"""
        try:
            response = self._clob_request('GET', f'/midpoint', {'token_id': token_id})
            return float(response.get('mid', 0))
        except Exception:
            return None

    def get_book(self, token_id: str) -> dict:
        """Get order book for a token"""
        return self._clob_request('GET', '/book', {'token_id': token_id})

    def get_all_active_markets(self, tag_id: int = None) -> list:
        """Fetch all active markets with offset-based pagination, optionally filtered by tag"""
        all_markets = []
        offset = 0
        limit = 100

        while True:
            try:
                response = self.get_markets(offset=offset, limit=limit, active=True, tag_id=tag_id)
            except Exception as e:
                logger.error(f"Failed to fetch markets at offset {offset}: {e}")
                break

            # Handle both list and dict responses
            if isinstance(response, list):
                markets = response
            elif isinstance(response, dict):
                markets = response.get('data', [])
                if isinstance(markets, dict):
                    markets = [markets]
            else:
                markets = []

            if not markets:
                break

            all_markets.extend(markets)
            logger.info(f"Fetched {len(markets)} Polymarket markets (total: {len(all_markets)})")

            # If we got fewer than limit, we've reached the end
            if len(markets) < limit:
                break

            offset += limit

        return all_markets

    def get_all_active_events(self) -> list:
        """Fetch all active events with offset-based pagination"""
        all_events = []
        offset = 0
        limit = 100

        while True:
            try:
                response = self.get_events(offset=offset, limit=limit, active=True)
            except Exception as e:
                logger.error(f"Failed to fetch events at offset {offset}: {e}")
                break

            if isinstance(response, list):
                events = response
            elif isinstance(response, dict):
                events = response.get('data', [])
                if isinstance(events, dict):
                    events = [events]
            else:
                events = []

            if not events:
                break

            all_events.extend(events)

            if len(events) < limit:
                break

            offset += limit

        return all_events

    def get_tags(self, limit: int = 100) -> list:
        """Get all available tags"""
        params = {'limit': limit}
        return self._gamma_request('/tags', params)

    def get_tag_by_slug(self, slug: str) -> dict:
        """Get tag by slug"""
        return self._gamma_request(f'/tags/slug/{slug}')
