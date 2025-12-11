#!/usr/bin/env python3
"""
Standalone Kalshi API Sample Script

This script demonstrates:
1. Querying market data for today's NYC weather
2. Querying the orderbook for that market
3. Placing and canceling an order of 1 unit

API keys are loaded from environment variables (same as the main application).
"""

import os
import sys
import base64
import datetime
import time
import json
import requests
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

# Cryptography imports for RSA signing
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding


class KalshiClient:
    """Standalone Kalshi API Client"""

    HOST = 'https://api.elections.kalshi.com'
    API_PATH = '/trade-api/v2'
    BASE_URL = HOST + API_PATH
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self, api_key_id: str = None, private_key_pem: str = None):
        self.api_key_id = api_key_id or os.environ.get('KALSHI_API_KEY_ID', '').strip('"\'')
        private_key_str = private_key_pem or os.environ.get('KALSHI_PRIVATE_KEY', '')

        self.private_key = None
        if private_key_str and len(private_key_str) > 100:
            try:
                private_key_str = private_key_str.strip('"\'')
                private_key_str = private_key_str.replace('\\n', '\n')
                self.private_key = serialization.load_pem_private_key(
                    private_key_str.encode('utf-8'),
                    password=None,
                    backend=default_backend()
                )
                print("✓ Private key loaded successfully")
            except Exception as e:
                print(f"✗ Could not load Kalshi private key: {e}")
        else:
            print("✗ No valid private key found in environment")

        if self.api_key_id:
            print(f"✓ API Key ID loaded: {self.api_key_id[:8]}...")
        else:
            print("✗ No API Key ID found in environment")

    def _create_signature(self, timestamp: str, method: str, path: str, debug: bool = False) -> str:
        """Create RSA-PSS signature for request"""
        if not self.private_key:
            return ''

        path_without_query = path.split('?')[0]
        message_str = f"{timestamp}{method}{path_without_query}"
        message = message_str.encode('utf-8')

        if debug:
            print(f"  [DEBUG] Signing message: {message_str}")

        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')

    def _get_headers(self, method: str, path: str, debug: bool = False) -> dict:
        """Get headers for request (authenticated if possible)"""
        headers = {'Content-Type': 'application/json'}

        if self.private_key and self.api_key_id:
            # Use time.time() for millisecond timestamp (matching official SDK)
            timestamp = str(int(time.time() * 1000))
            signature = self._create_signature(timestamp, method, path, debug=debug)
            headers.update({
                'KALSHI-ACCESS-KEY': self.api_key_id,
                'KALSHI-ACCESS-SIGNATURE': signature,
                'KALSHI-ACCESS-TIMESTAMP': timestamp,
            })

        return headers

    def _request(self, method: str, path: str, params: dict = None, body: dict = None, debug: bool = False) -> dict:
        """Make request to Kalshi API with retry logic"""
        # Full path for signing includes API_PATH prefix
        full_path = self.API_PATH + path
        url = self.HOST + full_path

        if params:
            query_parts = []
            for k, v in params.items():
                if v is not None:
                    query_parts.append(f"{k}={v}")
            if query_parts:
                full_path = full_path + '?' + '&'.join(query_parts)
                url = self.HOST + full_path

        if debug:
            print(f"  [DEBUG] URL: {url}")
            print(f"  [DEBUG] Full path for signing: {full_path}")

        # Sign the full path (including /trade-api/v2 prefix)
        headers = self._get_headers(method, full_path, debug=debug)

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                if body:
                    response = requests.request(method, url, headers=headers, json=body, timeout=30)
                else:
                    response = requests.request(method, url, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                last_error = e
                print(f"  API attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))

        raise last_error

    # ========== Market Data Methods ==========

    def get_markets(self, status: str = 'open', limit: int = 200, cursor: str = None,
                    event_ticker: str = None, series_ticker: str = None) -> dict:
        """Get markets from Kalshi"""
        params = {
            'status': status,
            'limit': limit,
            'cursor': cursor,
            'event_ticker': event_ticker,
            'series_ticker': series_ticker
        }
        return self._request('GET', '/markets', params)

    def get_market(self, ticker: str) -> dict:
        """Get single market by ticker"""
        return self._request('GET', f'/markets/{ticker}')

    def search_markets(self, query: str) -> list:
        """Search for markets by query string"""
        all_markets = []
        cursor = None

        while True:
            response = self.get_markets(status='open', cursor=cursor)
            markets = response.get('markets', [])

            # Filter by query
            for market in markets:
                title = market.get('title', '').lower()
                ticker = market.get('ticker', '').lower()
                if query.lower() in title or query.lower() in ticker:
                    all_markets.append(market)

            cursor = response.get('cursor')
            if not cursor or not markets:
                break

        return all_markets

    # ========== Orderbook Methods ==========

    def get_orderbook(self, ticker: str, depth: int = 10) -> dict:
        """
        Get the orderbook for a market.

        Args:
            ticker: Market ticker
            depth: Depth of orderbook (0 = all levels, 1-100 for specific depth)

        Returns:
            Orderbook with 'yes' and 'no' arrays of [price, quantity] levels
        """
        params = {'depth': depth} if depth > 0 else None
        return self._request('GET', f'/markets/{ticker}/orderbook', params)

    # ========== Order Methods ==========

    def create_order(self, ticker: str, side: str, action: str, count: int,
                     order_type: str = 'limit', yes_price: int = None, no_price: int = None,
                     debug: bool = False) -> dict:
        """
        Create an order on a market.

        Args:
            ticker: Market ticker
            side: 'yes' or 'no'
            action: 'buy' or 'sell'
            count: Number of contracts (minimum 1)
            order_type: 'limit' or 'market'
            yes_price: Price in cents (1-99) for yes side
            no_price: Price in cents (1-99) for no side
            debug: Print debug info for signature

        Returns:
            Order response with order details
        """
        body = {
            'ticker': ticker,
            'side': side,
            'action': action,
            'count': count,
            'type': order_type,
        }

        if yes_price is not None:
            body['yes_price'] = yes_price
        if no_price is not None:
            body['no_price'] = no_price

        return self._request('POST', '/portfolio/orders', body=body, debug=debug)

    def cancel_order(self, order_id: str) -> dict:
        """
        Cancel an existing order.

        Args:
            order_id: The order ID to cancel

        Returns:
            Cancel response with order details and reduced_by count
        """
        return self._request('DELETE', f'/portfolio/orders/{order_id}')

    def get_orders(self, status: str = None) -> dict:
        """
        Get user's orders.

        Args:
            status: Filter by status ('resting', 'canceled', 'executed')

        Returns:
            List of orders
        """
        params = {'status': status} if status else None
        return self._request('GET', '/portfolio/orders', params)


def find_nyc_weather_market(client: KalshiClient) -> dict:
    """Find a market for today's NYC weather"""
    print("\n" + "="*60)
    print("STEP 1: Finding NYC Weather Market")
    print("="*60)

    # Get today's date for filtering
    today = datetime.date.today()
    print(f"Looking for NYC weather markets for {today}...")

    # Search for NYC weather markets
    # Common series tickers: HIGHNY (NYC high temp), KXNYC (NYC weather)
    search_terms = ['HIGHNY', 'KXNYC', 'NYC', 'New York']

    found_markets = []
    for term in search_terms:
        print(f"  Searching for '{term}'...")
        try:
            # Try series ticker first
            response = client.get_markets(status='open', series_ticker=term)
            markets = response.get('markets', [])
            if markets:
                print(f"    Found {len(markets)} markets with series_ticker={term}")
                found_markets.extend(markets)
        except Exception as e:
            print(f"    Series search failed: {e}")

    if not found_markets:
        # Fallback: search through all markets
        print("  Falling back to full market search...")
        markets = client.search_markets('NYC')
        markets.extend(client.search_markets('New York'))
        found_markets = [m for m in markets if 'weather' in m.get('title', '').lower()
                        or 'temp' in m.get('title', '').lower()
                        or 'high' in m.get('title', '').lower()]

    # Filter for today's markets
    today_markets = []
    for market in found_markets:
        # Check if market closes today or is about today
        close_time_str = market.get('close_time', '')
        if close_time_str:
            try:
                close_time = datetime.datetime.fromisoformat(close_time_str.replace('Z', '+00:00'))
                if close_time.date() == today:
                    today_markets.append(market)
            except:
                pass

    if today_markets:
        print(f"\nFound {len(today_markets)} NYC weather markets for today:")
        for m in today_markets[:5]:
            print(f"  - {m.get('ticker')}: {m.get('title')}")
        return today_markets[0]
    elif found_markets:
        print(f"\nNo markets for today, but found {len(found_markets)} related markets:")
        for m in found_markets[:5]:
            print(f"  - {m.get('ticker')}: {m.get('title')}")
        return found_markets[0]
    else:
        print("\n✗ No NYC weather markets found")
        return None


def display_orderbook(client: KalshiClient, ticker: str):
    """Display the orderbook for a market"""
    print("\n" + "="*60)
    print(f"STEP 2: Getting Orderbook for {ticker}")
    print("="*60)

    try:
        response = client.get_orderbook(ticker, depth=10)
        orderbook = response.get('orderbook', {})

        yes_levels = orderbook.get('yes', [])
        no_levels = orderbook.get('no', [])

        print("\nYES Side (Bids):")
        print("  Price (¢) | Quantity")
        print("  " + "-"*22)
        if yes_levels:
            for level in yes_levels[:5]:
                price = level[0] if isinstance(level, list) else level.get('price', 0)
                qty = level[1] if isinstance(level, list) else level.get('quantity', 0)
                print(f"  {price:8} | {qty}")
        else:
            print("  (empty)")

        print("\nNO Side (Asks):")
        print("  Price (¢) | Quantity")
        print("  " + "-"*22)
        if no_levels:
            for level in no_levels[:5]:
                price = level[0] if isinstance(level, list) else level.get('price', 0)
                qty = level[1] if isinstance(level, list) else level.get('quantity', 0)
                print(f"  {price:8} | {qty}")
        else:
            print("  (empty)")

        return orderbook
    except Exception as e:
        print(f"✗ Failed to get orderbook: {e}")
        return None


def place_and_cancel_order(client: KalshiClient, ticker: str, orderbook: dict):
    """Place a limit order and then cancel it"""
    print("\n" + "="*60)
    print(f"STEP 3: Placing and Canceling Order on {ticker}")
    print("="*60)

    # Determine a safe price from the orderbook (far from market to avoid execution)
    # Use a very low price for a YES buy order so it won't execute
    yes_price = 1  # 1 cent - very unlikely to execute

    print(f"\nPlacing limit order:")
    print(f"  Side: YES")
    print(f"  Action: BUY")
    print(f"  Count: 1 contract")
    print(f"  Price: {yes_price}¢")

    try:
        # Place the order (with debug enabled to see signature details)
        order_response = client.create_order(
            ticker=ticker,
            side='yes',
            action='buy',
            count=1,
            order_type='limit',
            yes_price=yes_price,
            debug=True
        )

        order = order_response.get('order', {})
        order_id = order.get('order_id')

        print(f"\n✓ Order placed successfully!")
        print(f"  Order ID: {order_id}")
        print(f"  Status: {order.get('status')}")
        print(f"  Remaining: {order.get('remaining_count')} contracts")

        # Wait a moment
        print("\nWaiting 2 seconds before canceling...")
        time.sleep(2)

        # Cancel the order
        print(f"\nCanceling order {order_id}...")
        cancel_response = client.cancel_order(order_id)

        canceled_order = cancel_response.get('order', {})
        reduced_by = cancel_response.get('reduced_by', 0)

        print(f"\n✓ Order canceled successfully!")
        print(f"  Order ID: {canceled_order.get('order_id')}")
        print(f"  Status: {canceled_order.get('status')}")
        print(f"  Reduced by: {reduced_by} contracts")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"\n✗ Order operation failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"  Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"  Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n✗ Order operation failed: {e}")
        return False


def main():
    print("="*60)
    print("Kalshi API Sample Script")
    print("="*60)
    print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize client
    print("\nInitializing Kalshi client...")
    client = KalshiClient()

    if not client.private_key or not client.api_key_id:
        print("\n" + "="*60)
        print("ERROR: Missing API credentials")
        print("="*60)
        print("Please set the following environment variables in your .env file:")
        print("  KALSHI_API_KEY_ID=your-api-key-id")
        print("  KALSHI_PRIVATE_KEY=your-private-key-pem")
        print("\nYou can get these from: https://kalshi.com/settings/api")
        sys.exit(1)

    # Step 1: Find NYC weather market
    market = find_nyc_weather_market(client)

    if not market:
        print("\nCould not find a suitable NYC weather market.")
        print("Attempting to use a sample market for demonstration...")
        # Try to get any open market as fallback
        try:
            response = client.get_markets(status='open', limit=1)
            markets = response.get('markets', [])
            if markets:
                market = markets[0]
                print(f"Using fallback market: {market.get('ticker')} - {market.get('title')}")
        except Exception as e:
            print(f"Failed to get any market: {e}")
            sys.exit(1)

    ticker = market.get('ticker')
    print(f"\nSelected market: {ticker}")
    print(f"Title: {market.get('title')}")
    print(f"Status: {market.get('status')}")

    # Step 2: Get orderbook
    orderbook = display_orderbook(client, ticker)

    # Step 3: Place and cancel order
    if orderbook:
        success = place_and_cancel_order(client, ticker, orderbook)

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"✓ Market data retrieved: {ticker}")
        print(f"✓ Orderbook retrieved")
        if success:
            print(f"✓ Order placed and canceled successfully")
        else:
            print(f"✗ Order operations failed (may require funded account)")
    else:
        print("\nSkipping order operations due to orderbook failure.")

    print("\nScript completed.")


if __name__ == '__main__':
    main()
