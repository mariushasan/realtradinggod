from datetime import datetime
from typing import List, Dict, Optional
import logging
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.utils import timezone

from markets.models import Market, Exchange, Tag
from markets.api import KalshiClient, PolymarketClient

logger = logging.getLogger(__name__)


class MarketSyncService:
    """Service to sync market data from exchanges to database"""

    def __init__(self):
        self.kalshi_client = KalshiClient()
        self.poly_client = PolymarketClient()

    def sync_kalshi_tags(self) -> List[Tag]:
        """Fetch Kalshi tags from API and save to database"""
        synced = []
        try:
            response = self.kalshi_client.get_tags_by_categories()
            if not isinstance(response, dict):
                return synced

            tags_by_categories = response.get('tags_by_categories', {})
            if not isinstance(tags_by_categories, dict):
                return synced

            for category, tag_labels in tags_by_categories.items():
                # Skip None or empty categories
                if not tag_labels or not isinstance(tag_labels, list):
                    continue

                for label in tag_labels:
                    if not isinstance(label, str) or not label.strip():
                        continue

                    tag, created = Tag.objects.update_or_create(
                        exchange=Exchange.KALSHI,
                        label=label.strip(),
                        category=category,
                        defaults={
                            'slug': label.strip().lower().replace(' ', '-'),
                            'external_id': ''  # Kalshi tags don't have IDs
                        }
                    )
                    synced.append(tag)

            logger.info(f"Synced {len(synced)} Kalshi tags")
        except Exception as e:
            logger.error(f"Error syncing Kalshi tags: {e}")

        return synced

    def sync_polymarket_tags(self) -> List[Tag]:
        """Fetch Polymarket tags from API and save to database"""
        synced = []
        try:
            tags_data = self.poly_client.get_tags()
            if not isinstance(tags_data, list):
                return synced

            for tag_data in tags_data:
                if not isinstance(tag_data, dict):
                    continue

                # Skip hidden tags
                if tag_data.get('forceHide', False):
                    continue

                label = tag_data.get('label', '').strip()
                if not label:
                    continue

                tag, created = Tag.objects.update_or_create(
                    exchange=Exchange.POLYMARKET,
                    label=label,
                    category='',  # Polymarket tags don't have categories
                    defaults={
                        'external_id': str(tag_data.get('id', '')),
                        'slug': tag_data.get('slug', '')
                    }
                )
                synced.append(tag)

            logger.info(f"Synced {len(synced)} Polymarket tags")
        except Exception as e:
            logger.error(f"Error syncing Polymarket tags: {e}")

        return synced

    def sync_all_tags(self) -> Dict[str, List[Tag]]:
        """Sync tags from both exchanges"""
        return {
            'kalshi': self.sync_kalshi_tags(),
            'polymarket': self.sync_polymarket_tags()
        }

    def get_kalshi_tags_from_db(self) -> List[Tag]:
        """Get Kalshi tags from database"""
        return list(Tag.objects.filter(exchange=Exchange.KALSHI).order_by('category', 'label'))

    def get_polymarket_tags_from_db(self) -> List[Tag]:
        """Get Polymarket tags from database"""
        return list(Tag.objects.filter(exchange=Exchange.POLYMARKET).order_by('label'))

    def _extract_kalshi_price(self, dollars_value, cents_value) -> float:
        """
        Safely extract price from Kalshi API response.

        Prefers the _dollars field (string like "0.5600") over cent values.
        Returns price as a float between 0 and 1.
        """
        # Try dollars value first (string format like "0.5600")
        if dollars_value is not None:
            try:
                price = float(dollars_value)
                # Sanity check - price should be between 0 and 1
                if 0 <= price <= 1:
                    return price
                # If > 1, might be in wrong format, log and fall through
                logger.warning(f"Kalshi dollars value out of range: {dollars_value}")
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not parse Kalshi dollars value '{dollars_value}': {e}")

        # Fall back to cents value (integer 0-100)
        if cents_value is not None:
            try:
                cents = float(cents_value)
                # Kalshi cents are 0-100 representing probability percentage
                if 0 <= cents <= 100:
                    return cents / 100
                elif cents > 100:
                    # Might be basis points (0-10000), convert accordingly
                    logger.warning(f"Kalshi cents value > 100: {cents_value}, treating as basis points")
                    return cents / 10000
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not parse Kalshi cents value '{cents_value}': {e}")

        # Default to 0 if both fail
        return 0.0

    def sync_kalshi_markets(self, tag_slugs: Optional[List[str]] = None) -> List[Market]:
        """
        Sync markets from Kalshi, optionally filtered by tag slugs.

        Kalshi's API structure requires a two-step process:
        1. Get series that match the selected categories (tags belong to categories)
        2. Get markets for those series
        """
        synced = []

        # Get Tag objects for the selected slugs
        tag_objects = []
        categories = set()
        if tag_slugs:
            tag_objects = list(Tag.objects.filter(
                exchange=Exchange.KALSHI,
                slug__in=tag_slugs
            ))
            # Get unique categories from the selected tags
            for tag in tag_objects:
                if tag.category:
                    categories.add(tag.category)

        try:
            markets_data = []
            seen_tickers = set()

            if categories:
                # Step 1: Get series for each category
                logger.info(f"Fetching series for Kalshi categories: {categories}")
                series_tickers = set()
                for category in categories:
                    try:
                        response = self.kalshi_client.get_series(category=category)
                        series_list = response.get('series', [])
                        for series in series_list:
                            ticker = series.get('ticker', '')
                            if ticker:
                                series_tickers.add(ticker)
                    except Exception as e:
                        logger.warning(f"Failed to fetch series for category {category}: {e}")

                logger.info(f"Found {len(series_tickers)} series tickers for selected categories")

                # Step 2: Get markets for each series
                for series_ticker in series_tickers:
                    try:
                        series_markets = self.kalshi_client.get_markets_by_series(series_ticker)
                        for market in series_markets:
                            ticker = market.get('ticker', '')
                            if ticker and ticker not in seen_tickers:
                                markets_data.append(market)
                                seen_tickers.add(ticker)
                    except Exception as e:
                        logger.warning(f"Failed to fetch markets for series {series_ticker}: {e}")
            else:
                # No filter - fetch all open markets
                markets_data = self.kalshi_client.get_all_open_markets()

            logger.info(f"Processing {len(markets_data)} Kalshi markets")

            for market_data in markets_data:
                ticker = market_data.get('ticker', '')
                if not ticker:
                    continue

                event_ticker = market_data.get('event_ticker', '')

                # Extract prices - prefer _dollars fields (string format like "0.5600")
                # Fall back to cent values if _dollars not available
                yes_price = self._extract_kalshi_price(
                    market_data.get('yes_ask_dollars'),
                    market_data.get('yes_ask')
                )
                no_price = self._extract_kalshi_price(
                    market_data.get('no_ask_dollars'),
                    market_data.get('no_ask')
                )

                outcomes = [
                    {'name': 'Yes', 'price': yes_price},
                    {'name': 'No', 'price': no_price}
                ]

                # Build URL - Kalshi uses event ticker in URL
                url = f"https://kalshi.com/markets/{event_ticker}" if event_ticker else ''

                # Parse close time
                close_time = None
                close_time_str = market_data.get('close_time')
                if close_time_str:
                    try:
                        close_time = datetime.fromisoformat(
                            close_time_str.replace('Z', '+00:00')
                        )
                    except Exception:
                        pass

                # Determine if market is active
                # Kalshi statuses: active, open, finalized, settled, closed
                market_status = market_data.get('status', '')
                is_active = market_status in ['active', 'open']

                try:
                    market, created = Market.objects.update_or_create(
                        exchange=Exchange.KALSHI,
                        external_id=ticker,
                        defaults={
                            'event_external_id': event_ticker,
                            'title': market_data.get('title', ticker),
                            'description': market_data.get('rules_primary', ''),
                            'outcomes': outcomes,
                            'url': url,
                            'is_active': is_active,
                            'close_time': close_time
                        }
                    )

                    # Associate market with the tags used for syncing
                    if tag_objects:
                        market.tags.add(*tag_objects)

                    synced.append(market)
                    if created:
                        logger.debug(f"Created new Kalshi market: {ticker}")
                except Exception as e:
                    logger.error(f"Failed to save Kalshi market {ticker}: {e}")

        except Exception as e:
            logger.error(f"Error syncing Kalshi markets: {e}")
            raise

        logger.info(f"Successfully synced {len(synced)} Kalshi markets to database")
        return synced

    def sync_polymarket_markets(self, tag_ids: Optional[List[int]] = None) -> List[Market]:
        """Sync markets from Polymarket, optionally filtered by tag IDs"""
        synced = []

        # Get Tag objects for the selected external_ids
        tag_objects = []
        if tag_ids:
            tag_id_strs = [str(t) for t in tag_ids]
            tag_objects = list(Tag.objects.filter(
                exchange=Exchange.POLYMARKET,
                external_id__in=tag_id_strs
            ))

        try:
            # If tag_ids provided, fetch markets for each tag
            if tag_ids:
                markets_data = []
                seen_condition_ids = set()
                for tag_id in tag_ids:
                    tag_markets = self.poly_client.get_all_active_markets(tag_id=tag_id)
                    for market in tag_markets:
                        condition_id = market.get('conditionId', market.get('condition_id', ''))
                        if condition_id and condition_id not in seen_condition_ids:
                            markets_data.append(market)
                            seen_condition_ids.add(condition_id)
            else:
                markets_data = self.poly_client.get_all_active_markets()

            for market_data in markets_data:
                condition_id = market_data.get('conditionId', market_data.get('condition_id', ''))
                if not condition_id:
                    continue

                # Extract outcomes and prices
                outcomes = []

                # Handle JSON string format from Gamma API
                outcome_names = market_data.get('outcomes', '[]')
                outcome_prices = market_data.get('outcomePrices', '[]')

                if isinstance(outcome_names, str):
                    try:
                        outcome_names = json.loads(outcome_names)
                    except json.JSONDecodeError:
                        outcome_names = []

                if isinstance(outcome_prices, str):
                    try:
                        outcome_prices = json.loads(outcome_prices)
                    except json.JSONDecodeError:
                        outcome_prices = []

                # Build outcomes list
                for i, name in enumerate(outcome_names):
                    price = float(outcome_prices[i]) if i < len(outcome_prices) else 0
                    outcomes.append({
                        'name': name,
                        'price': price
                    })

                # Fallback to tokens format
                if not outcomes:
                    tokens = market_data.get('tokens', [])
                    for token in tokens:
                        outcome_name = token.get('outcome', '')
                        price = float(token.get('price', 0))
                        outcomes.append({
                            'name': outcome_name,
                            'price': price,
                            'token_id': token.get('token_id', '')
                        })

                # Build URL from slug
                # Polymarket URL format: https://polymarket.com/event/[slug]
                slug = market_data.get('slug', '')
                url = f"https://polymarket.com/event/{slug}" if slug else ''

                # Parse close time
                close_time = None
                end_date = market_data.get('endDate', market_data.get('end_date_iso'))
                if end_date:
                    try:
                        close_time = datetime.fromisoformat(
                            end_date.replace('Z', '+00:00')
                        )
                    except Exception:
                        pass

                market, created = Market.objects.update_or_create(
                    exchange=Exchange.POLYMARKET,
                    external_id=condition_id,
                    defaults={
                        'event_external_id': slug,  # Store slug for URL building
                        'title': market_data.get('question', market_data.get('title', '')),
                        'description': market_data.get('description', ''),
                        'outcomes': outcomes,
                        'url': url,
                        'is_active': market_data.get('active', True),
                        'close_time': close_time
                    }
                )

                # Associate market with the tags used for syncing
                if tag_objects:
                    market.tags.add(*tag_objects)

                synced.append(market)

        except Exception as e:
            logger.error(f"Error syncing Polymarket markets: {e}")
            raise

        return synced

    def sync_all(
        self,
        kalshi_tag_slugs: Optional[List[str]] = None,
        polymarket_tag_ids: Optional[List[int]] = None
    ) -> Dict[str, List[Market]]:
        """Sync markets from all exchanges in parallel, with optional tag filtering"""
        results = {
            'kalshi': [],
            'polymarket': []
        }

        # Run both syncs in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(self.sync_kalshi_markets, kalshi_tag_slugs): 'kalshi',
                executor.submit(self.sync_polymarket_markets, polymarket_tag_ids): 'polymarket'
            }

            for future in as_completed(futures):
                exchange = futures[future]
                try:
                    results[exchange] = future.result()
                    logger.info(f"Synced {len(results[exchange])} {exchange} markets")
                except Exception as e:
                    logger.error(f"{exchange} sync failed: {e}")

        return results
