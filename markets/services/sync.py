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

    def sync_kalshi_markets(self, series_tickers: Optional[List[str]] = None) -> List[Market]:
        """Sync markets from Kalshi, optionally filtered by series tickers (tags)"""
        synced = []

        # Get Tag objects for the selected slugs
        tag_objects = []
        if series_tickers:
            tag_objects = list(Tag.objects.filter(
                exchange=Exchange.KALSHI,
                slug__in=series_tickers
            ))

        try:
            # If series_tickers provided, fetch events for each series
            if series_tickers:
                events = []
                seen_event_tickers = set()
                for series_ticker in series_tickers:
                    series_events = self.kalshi_client.get_all_open_events(series_ticker=series_ticker)
                    for event in series_events:
                        event_ticker = event.get('event_ticker', '')
                        if event_ticker not in seen_event_tickers:
                            events.append(event)
                            seen_event_tickers.add(event_ticker)
            else:
                events = self.kalshi_client.get_all_open_events()

            for event in events:
                event_ticker = event.get('event_ticker', '')
                markets = event.get('markets', [])

                for market_data in markets:
                    ticker = market_data.get('ticker', '')
                    if not ticker:
                        continue

                    # Extract prices
                    yes_ask = market_data.get('yes_ask', 0)
                    no_ask = market_data.get('no_ask', 0)

                    # Convert from cents to decimal if needed
                    if yes_ask and yes_ask > 1:
                        yes_ask = yes_ask / 100
                    if no_ask and no_ask > 1:
                        no_ask = no_ask / 100

                    outcomes = [
                        {'name': 'Yes', 'price': yes_ask},
                        {'name': 'No', 'price': no_ask}
                    ]

                    # Build URL - Kalshi uses event ticker in URL
                    # Format: https://kalshi.com/markets/EVENT_TICKER
                    url = f"https://kalshi.com/markets/{event_ticker}"

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

                    market, created = Market.objects.update_or_create(
                        exchange=Exchange.KALSHI,
                        external_id=ticker,
                        defaults={
                            'event_external_id': event_ticker,
                            'title': market_data.get('title', ticker),
                            'description': market_data.get('rules_primary', ''),
                            'outcomes': outcomes,
                            'url': url,
                            'is_active': market_data.get('status') in ['active', 'open'],
                            'close_time': close_time
                        }
                    )

                    # Associate market with the tags used for syncing
                    if tag_objects:
                        market.tags.add(*tag_objects)

                    synced.append(market)

        except Exception as e:
            logger.error(f"Error syncing Kalshi markets: {e}")
            raise

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
        kalshi_series_tickers: Optional[List[str]] = None,
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
                executor.submit(self.sync_kalshi_markets, kalshi_series_tickers): 'kalshi',
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
