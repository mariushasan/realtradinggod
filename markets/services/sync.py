from datetime import datetime
from typing import List, Dict, Optional
import logging
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.utils import timezone

from markets.models import Market, Event, Exchange, Tag, TagMatch
from markets.api import KalshiClient, PolymarketClient

logger = logging.getLogger(__name__)


class EventSyncService:
    """Service to sync event data from exchanges to database"""

    def __init__(self):
        self.kalshi_client = KalshiClient()
        self.poly_client = PolymarketClient()

    def sync_kalshi_tags(self) -> List[Tag]:
        """Fetch Kalshi tags from API and save to database using bulk operations"""
        tags_to_create = []
        try:
            response = self.kalshi_client.get_tags_by_categories()
            if not isinstance(response, dict):
                return []

            tags_by_categories = response.get('tags_by_categories', {})
            if not isinstance(tags_by_categories, dict):
                return []

            for category, tag_labels in tags_by_categories.items():
                # Skip None or empty categories
                if not tag_labels or not isinstance(tag_labels, list):
                    continue

                for label in tag_labels:
                    if not isinstance(label, str) or not label.strip():
                        continue

                    tags_to_create.append(Tag(
                        exchange=Exchange.KALSHI,
                        label=label.strip(),
                        category=category or '',
                        slug=label.strip(),
                        external_id=''  # Kalshi tags don't have IDs
                    ))

            if tags_to_create:
                # Bulk create/update tags
                Tag.objects.bulk_create(
                    tags_to_create,
                    update_conflicts=True,
                    unique_fields=['exchange', 'label', 'category'],
                    update_fields=['slug', 'external_id']
                )

            logger.info(f"Synced {len(tags_to_create)} Kalshi tags")
        except Exception as e:
            logger.error(f"Error syncing Kalshi tags: {e}")

        return tags_to_create

    def sync_polymarket_tags(self) -> List[Tag]:
        """Fetch Polymarket tags from API and save to database using bulk operations"""
        tags_to_create = []
        try:
            tags_data = self.poly_client.get_tags()
            if not isinstance(tags_data, list):
                return []

            for tag_data in tags_data:
                if not isinstance(tag_data, dict):
                    continue

                # Skip hidden tags
                if tag_data.get('forceHide', False):
                    continue

                label = tag_data.get('label', '').strip()
                if not label:
                    continue

                tags_to_create.append(Tag(
                    exchange=Exchange.POLYMARKET,
                    label=label,
                    category='',  # Polymarket tags don't have categories
                    external_id=str(tag_data.get('id', '')),
                    slug=tag_data.get('slug', '')
                ))

            if tags_to_create:
                # Bulk create/update tags
                Tag.objects.bulk_create(
                    tags_to_create,
                    update_conflicts=True,
                    unique_fields=['exchange', 'label', 'category'],
                    update_fields=['external_id', 'slug']
                )

            logger.info(f"Synced {len(tags_to_create)} Polymarket tags")
        except Exception as e:
            logger.error(f"Error syncing Polymarket tags: {e}")

        return tags_to_create

    def sync_all_tags(self, auto_match: bool = True) -> Dict:
        """Sync tags from both exchanges"""
        result = {
            'kalshi': self.sync_kalshi_tags(),
            'polymarket': self.sync_polymarket_tags(),
            'tag_matches': []
        }

        return result

    def sync_kalshi_events(
        self,
        tag_slugs: Optional[List[str]] = None,
        close_after: Optional[str] = None,
        close_before: Optional[str] = None,
        volume_min: Optional[float] = None,
        volume_max: Optional[float] = None,
        liquidity_min: Optional[float] = None,
        liquidity_max: Optional[float] = None
    ) -> List[Event]:
        """
        Sync events from Kalshi with their nested markets using bulk operations.

        Args:
            tag_slugs: List of tag labels to filter by (uses exact tag name to get series)
            close_after: ISO date string (YYYY-MM-DD) - only sync events with markets closing after this date
            close_before: ISO date string (YYYY-MM-DD) - not directly supported by Kalshi events API
            volume_min: Minimum volume filter (client-side, API doesn't support)
            volume_max: Maximum volume filter (client-side, API doesn't support)
            liquidity_min: Minimum liquidity filter (client-side, API doesn't support)
            liquidity_max: Maximum liquidity filter (client-side, API doesn't support)
        """
        events_to_create = []
        markets_to_create = []
        event_market_map = {}  # Maps event external_id to list of market data

        # Convert date strings to Unix timestamps for Kalshi API
        min_close_ts = None
        if close_after:
            try:
                dt = datetime.strptime(close_after, '%Y-%m-%d')
                min_close_ts = int(dt.timestamp())
            except ValueError:
                logger.warning(f"Invalid close_after date format: {close_after}")

        try:
            # If tags provided, first get series tickers for those tags
            series_tickers = None
            if tag_slugs:
                series_tickers = self.kalshi_client.get_series_tickers_by_tags(tag_slugs)
                logger.info(f"Found {len(series_tickers)} series for tags: {tag_slugs}")
                if not series_tickers:
                    logger.warning("No series found for the given tags")
                    return []

            # Fetch events - either for specific series or all
            regular_events = []
            multivariate_events = []

            if series_tickers:
                # Fetch events for each series ticker
                for series_ticker in series_tickers:
                    series_regular = self.kalshi_client.get_all_open_events(
                        series_ticker=series_ticker,
                        min_close_ts=min_close_ts
                    )
                    regular_events.extend(series_regular)

                    series_multi = self.kalshi_client.get_all_multivariate_events(
                        series_ticker=series_ticker
                    )
                    multivariate_events.extend(series_multi)
            else:
                # Fetch all events
                regular_events = self.kalshi_client.get_all_open_events(min_close_ts=min_close_ts)
                multivariate_events = self.kalshi_client.get_all_multivariate_events()

            logger.info(f"Fetched {len(regular_events)} regular Kalshi events")
            logger.info(f"Fetched {len(multivariate_events)} multivariate Kalshi events")

            # Combine and deduplicate by event_ticker
            seen_tickers = set()
            events_data = []
            for event in regular_events + multivariate_events:
                ticker = event.get('event_ticker', '')
                if ticker and ticker not in seen_tickers:
                    seen_tickers.add(ticker)
                    events_data.append(event)

            logger.info(f"Processing {len(events_data)} total Kalshi events (deduplicated)")

            # Parse date filters for client-side filtering
            close_after_dt = None
            close_before_dt = None
            if close_after:
                try:
                    close_after_dt = datetime.strptime(close_after, '%Y-%m-%d')
                except ValueError:
                    pass
            if close_before:
                try:
                    close_before_dt = datetime.strptime(close_before, '%Y-%m-%d').replace(
                        hour=23, minute=59, second=59
                    )
                except ValueError:
                    pass

            # First pass: prepare all event objects
            for event_data in events_data:
                event_ticker = event_data.get('event_ticker', '')
                if not event_ticker:
                    continue

                markets = event_data.get('markets', [])

                # Find the latest close time among markets for this event
                event_close_time = None
                for market in markets:
                    close_time_str = market.get('close_time')
                    if close_time_str:
                        try:
                            market_close = datetime.fromisoformat(
                                close_time_str.replace('Z', '+00:00')
                            ).replace(tzinfo=None)
                            if event_close_time is None or market_close > event_close_time:
                                event_close_time = market_close
                        except Exception:
                            pass

                # Client-side date filtering (multivariate events don't support API filtering)
                if close_after_dt and event_close_time:
                    if event_close_time < close_after_dt:
                        continue  # Event closes before the "closes after" date, skip it

                if close_before_dt and event_close_time:
                    if event_close_time > close_before_dt:
                        continue  # Event closes after the "closes before" date, skip it

                # Build URL - Kalshi uses event ticker in URL
                url = f"https://kalshi.com/markets/{event_ticker}"

                # Use the already computed event_close_time as end_date
                end_date = event_close_time

                # Calculate aggregated volume from markets
                total_volume = sum(m.get('volume', 0) or 0 for m in markets)
                total_volume_24h = sum(m.get('volume_24h', 0) or 0 for m in markets)
                total_liquidity = sum(m.get('liquidity', 0) or 0 for m in markets)
                total_open_interest = sum(m.get('open_interest', 0) or 0 for m in markets)

                # Client-side volume/liquidity filtering (Kalshi API doesn't support these)
                if volume_min is not None and total_volume < volume_min:
                    continue
                if volume_max is not None and total_volume > volume_max:
                    continue
                if liquidity_min is not None and total_liquidity < liquidity_min:
                    continue
                if liquidity_max is not None and total_liquidity > liquidity_max:
                    continue

                # Create Event object (not saved yet)
                events_to_create.append(Event(
                    exchange=Exchange.KALSHI,
                    external_id=event_ticker,
                    title=event_data.get('title', event_ticker),
                    description=event_data.get('sub_title', ''),
                    category=event_data.get('category', ''),
                    url=url,
                    volume=total_volume,
                    volume_24h=total_volume_24h,
                    liquidity=total_liquidity,
                    open_interest=total_open_interest,
                    is_active=True,
                    mutually_exclusive=event_data.get('mutually_exclusive', False),
                    end_date=end_date
                ))

                # Store market data for this event
                event_market_map[event_ticker] = {
                    'markets': markets,
                    'url': url
                }

            # Bulk create/update events
            if events_to_create:
                Event.objects.bulk_create(
                    events_to_create,
                    update_conflicts=True,
                    unique_fields=['exchange', 'external_id'],
                    update_fields=[
                        'title', 'description', 'category', 'url',
                        'volume', 'volume_24h', 'liquidity', 'open_interest',
                        'is_active', 'mutually_exclusive', 'end_date'
                    ]
                )

            # Fetch all events from DB to get their IDs (needed for FK)
            event_ids = {e.external_id: e for e in Event.objects.filter(
                exchange=Exchange.KALSHI,
                external_id__in=event_market_map.keys()
            )}

            # Second pass: prepare all market objects
            for event_ticker, data in event_market_map.items():
                event = event_ids.get(event_ticker)
                if not event:
                    continue

                for market_data in data['markets']:
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

                    markets_to_create.append(Market(
                        exchange=Exchange.KALSHI,
                        external_id=ticker,
                        event=event,
                        event_external_id=event_ticker,
                        title=market_data.get('title', ticker),
                        description=market_data.get('rules_primary', ''),
                        outcomes=outcomes,
                        url=data['url'],
                        volume=market_data.get('volume', 0) or 0,
                        volume_24h=market_data.get('volume_24h', 0) or 0,
                        liquidity=market_data.get('liquidity', 0) or 0,
                        open_interest=market_data.get('open_interest', 0) or 0,
                        is_active=market_data.get('status') in ['active', 'open'],
                        close_time=close_time
                    ))

            # Bulk create/update markets
            if markets_to_create:
                Market.objects.bulk_create(
                    markets_to_create,
                    update_conflicts=True,
                    unique_fields=['exchange', 'external_id'],
                    update_fields=[
                        'event', 'event_external_id', 'title', 'description',
                        'outcomes', 'url', 'volume', 'volume_24h', 'liquidity',
                        'open_interest', 'is_active', 'close_time'
                    ]
                )

            logger.info(f"Synced {len(events_to_create)} Kalshi events with {len(markets_to_create)} markets")

        except Exception as e:
            logger.error(f"Error syncing Kalshi events: {e}")
            raise

        return events_to_create

    def sync_polymarket_events(
        self,
        tag_ids: Optional[List[int]] = None,
        close_after: Optional[str] = None,
        close_before: Optional[str] = None,
        volume_min: Optional[float] = None,
        volume_max: Optional[float] = None,
        liquidity_min: Optional[float] = None,
        liquidity_max: Optional[float] = None
    ) -> List[Event]:
        """
        Sync events from Polymarket with their nested markets using bulk operations.

        Args:
            tag_ids: List of tag IDs to filter by
            close_after: ISO date string (YYYY-MM-DD) - only sync events closing after this date
            close_before: ISO date string (YYYY-MM-DD) - only sync events closing before this date
            volume_min: Minimum volume filter
            volume_max: Maximum volume filter
            liquidity_min: Minimum liquidity filter
            liquidity_max: Maximum liquidity filter
        """
        events_to_create = []
        markets_to_create = []
        event_market_map = {}  # Maps event external_id to list of market data

        # Convert date strings to ISO 8601 format for Polymarket API
        end_date_min = None
        end_date_max = None
        if close_after:
            try:
                dt = datetime.strptime(close_after, '%Y-%m-%d')
                end_date_min = dt.strftime('%Y-%m-%dT00:00:00.000Z')
            except ValueError:
                logger.warning(f"Invalid close_after date format: {close_after}")
        if close_before:
            try:
                dt = datetime.strptime(close_before, '%Y-%m-%d')
                end_date_max = dt.strftime('%Y-%m-%dT23:59:59.999Z')
            except ValueError:
                logger.warning(f"Invalid close_before date format: {close_before}")

        try:
            # Fetch events - if tag_ids provided, fetch for each tag
            events_data = []
            if tag_ids:
                for tag_id in tag_ids:
                    tag_events = self.poly_client.get_all_active_events(
                        tag_id=tag_id,
                        end_date_min=end_date_min,
                        end_date_max=end_date_max,
                        volume_min=volume_min,
                        volume_max=volume_max,
                        liquidity_min=liquidity_min,
                        liquidity_max=liquidity_max
                    )
                    events_data.extend(tag_events)
                # Deduplicate by event ID
                seen_ids = set()
                unique_events = []
                for event in events_data:
                    event_id = event.get('id', '')
                    if event_id and event_id not in seen_ids:
                        seen_ids.add(event_id)
                        unique_events.append(event)
                events_data = unique_events
            else:
                events_data = self.poly_client.get_all_active_events(
                    end_date_min=end_date_min,
                    end_date_max=end_date_max,
                    volume_min=volume_min,
                    volume_max=volume_max,
                    liquidity_min=liquidity_min,
                    liquidity_max=liquidity_max
                )

            logger.info(f"Processing {len(events_data)} Polymarket events")

            # First pass: prepare all event objects
            for event_data in events_data:
                event_id = event_data.get('id', '')
                slug = event_data.get('slug', '')
                if not event_id and not slug:
                    continue

                external_id = event_id or slug

                # Build URL
                url = f"https://polymarket.com/event/{slug}" if slug else ''

                # Parse end date
                end_date = None
                end_date_str = event_data.get('endDate')
                if end_date_str:
                    try:
                        end_date = datetime.fromisoformat(
                            end_date_str.replace('Z', '+00:00')
                        )
                    except Exception:
                        pass

                # Create Event object (not saved yet)
                events_to_create.append(Event(
                    exchange=Exchange.POLYMARKET,
                    external_id=external_id,
                    title=event_data.get('title', slug),
                    description=event_data.get('description', ''),
                    category=event_data.get('category', ''),
                    url=url,
                    volume=float(event_data.get('volume', 0) or 0),
                    volume_24h=float(event_data.get('volume24hr', 0) or 0),
                    liquidity=float(event_data.get('liquidity', 0) or 0),
                    open_interest=float(event_data.get('openInterest', 0) or 0),
                    is_active=event_data.get('active', True),
                    mutually_exclusive=event_data.get('negRisk', False),
                    end_date=end_date
                ))

                # Store market data for this event
                event_market_map[external_id] = {
                    'markets': event_data.get('markets', []),
                    'slug': slug
                }

            # Bulk create/update events
            if events_to_create:
                Event.objects.bulk_create(
                    events_to_create,
                    update_conflicts=True,
                    unique_fields=['exchange', 'external_id'],
                    update_fields=[
                        'title', 'description', 'category', 'url',
                        'volume', 'volume_24h', 'liquidity', 'open_interest',
                        'is_active', 'mutually_exclusive', 'end_date'
                    ]
                )

            # Fetch all events from DB to get their IDs (needed for FK)
            event_ids = {e.external_id: e for e in Event.objects.filter(
                exchange=Exchange.POLYMARKET,
                external_id__in=event_market_map.keys()
            )}

            # Second pass: prepare all market objects
            for external_id, data in event_market_map.items():
                event = event_ids.get(external_id)
                if not event:
                    continue

                slug = data['slug']
                for market_data in data['markets']:
                    if not isinstance(market_data, dict):
                        continue

                    condition_id = market_data.get('conditionId', market_data.get('condition_id', ''))
                    market_id = market_data.get('id', '')
                    if not condition_id and not market_id:
                        continue

                    market_external_id = condition_id or market_id

                    # Extract outcomes and prices
                    outcomes = []
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

                    # Build market URL
                    market_url = f"https://polymarket.com/event/{slug}" if slug else ''

                    # Parse close time
                    close_time = None
                    market_end_date = market_data.get('endDate', market_data.get('end_date_iso'))
                    if market_end_date:
                        try:
                            close_time = datetime.fromisoformat(
                                market_end_date.replace('Z', '+00:00')
                            )
                        except Exception:
                            pass

                    markets_to_create.append(Market(
                        exchange=Exchange.POLYMARKET,
                        external_id=market_external_id,
                        event=event,
                        event_external_id=slug,
                        title=market_data.get('question', market_data.get('title', '')),
                        description=market_data.get('description', ''),
                        outcomes=outcomes,
                        url=market_url,
                        volume=float(market_data.get('volumeNum', market_data.get('volume', 0)) or 0),
                        volume_24h=float(market_data.get('volume24hr', 0) or 0),
                        liquidity=float(market_data.get('liquidityNum', market_data.get('liquidity', 0)) or 0),
                        open_interest=0,
                        is_active=market_data.get('active', True),
                        close_time=close_time
                    ))

            # Bulk create/update markets
            if markets_to_create:
                Market.objects.bulk_create(
                    markets_to_create,
                    update_conflicts=True,
                    unique_fields=['exchange', 'external_id'],
                    update_fields=[
                        'event', 'event_external_id', 'title', 'description',
                        'outcomes', 'url', 'volume', 'volume_24h', 'liquidity',
                        'open_interest', 'is_active', 'close_time'
                    ]
                )

            logger.info(f"Synced {len(events_to_create)} Polymarket events with {len(markets_to_create)} markets")

        except Exception as e:
            logger.error(f"Error syncing Polymarket events: {e}")
            raise

        return events_to_create

    def sync_all_events(
        self,
        kalshi_tag_slugs: Optional[List[str]] = None,
        polymarket_tag_ids: Optional[List[int]] = None,
        close_after: Optional[str] = None,
        close_before: Optional[str] = None,
        volume_min: Optional[float] = None,
        volume_max: Optional[float] = None,
        liquidity_min: Optional[float] = None,
        liquidity_max: Optional[float] = None
    ) -> Dict[str, List[Event]]:
        """Sync events from all exchanges in parallel, with optional filtering"""
        results = {
            'kalshi': [],
            'polymarket': []
        }

        # Run both syncs in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(
                    self.sync_kalshi_events,
                    kalshi_tag_slugs,
                    close_after,
                    close_before,
                    volume_min,
                    volume_max,
                    liquidity_min,
                    liquidity_max
                ): 'kalshi',
                executor.submit(
                    self.sync_polymarket_events,
                    polymarket_tag_ids,
                    close_after,
                    close_before,
                    volume_min,
                    volume_max,
                    liquidity_min,
                    liquidity_max
                ): 'polymarket'
            }

            for future in as_completed(futures):
                exchange = futures[future]
                try:
                    results[exchange] = future.result()
                    logger.info(f"Synced {len(results[exchange])} {exchange} events")
                except Exception as e:
                    logger.error(f"{exchange} sync failed: {e}")

        return results


# Keep MarketSyncService as an alias for backwards compatibility
MarketSyncService = EventSyncService
