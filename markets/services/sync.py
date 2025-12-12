from datetime import datetime
from typing import List, Dict, Optional
import logging
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.utils import timezone

from markets.models import Market, Event, Exchange
from markets.api import KalshiClient, PolymarketClient

logger = logging.getLogger(__name__)

# Batch size for bulk operations
BATCH_SIZE = 500


class EventSyncService:
    """Service to sync event data from exchanges to database"""

    def __init__(self):
        self.kalshi_client = KalshiClient()
        self.poly_client = PolymarketClient()
        self.debug = False
        # Debug: save first 5 event_data samples for each exchange
        self._kalshi_events_saved = 0
        self._polymarket_events_saved = 0
        self._debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'event_debug')

    def _bulk_create_events(self, events: List[Event], exchange: Exchange) -> Dict[str, Event]:
        """Bulk create/update events and return a dict mapping external_id to Event"""

        if not events:
            return {}

        Event.objects.bulk_create(
            events,
            update_conflicts=True,
            unique_fields=['exchange', 'external_id'],
            update_fields=[
                'title', 'description', 'category', 'url',
                'volume', 'volume_24h', 'liquidity', 'open_interest',
                'is_active', 'mutually_exclusive', 'end_date'
            ]
        )

        # Fetch created/updated events to get their IDs
        external_ids = [e.external_id for e in events]
        return {
            e.external_id: e for e in Event.objects.filter(
                exchange=exchange,
                external_id__in=external_ids
            )
        }

    def _bulk_create_markets(self, markets: List[Market]) -> None:
        """Bulk create/update markets"""
        if not markets:
            return

        Market.objects.bulk_create(
            markets,
            update_conflicts=True,
            unique_fields=['exchange', 'external_id'],
            update_fields=[
                'event', 'event_external_id', 'title', 'description',
                'outcomes', 'url', 'volume', 'volume_24h', 'liquidity',
                'open_interest', 'is_active', 'close_time'
            ]
        )

    def _flush_kalshi_batch(
        self,
        events_batch: List[Event],
        market_data_batch: Dict[str, dict],
        total_events: List[int]
    ) -> None:
        """Flush a batch of Kalshi events and their markets to the database"""
        if not events_batch:
            return

        # Bulk create events and get their IDs
        event_ids = self._bulk_create_events(events_batch, Exchange.KALSHI)
        total_events[0] += len(events_batch)

        # Create markets for this batch
        markets_to_create = []
        for event_ticker, data in market_data_batch.items():
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

        # Bulk create markets
        self._bulk_create_markets(markets_to_create)
        logger.info(f"Flushed batch: {len(events_batch)} events, {len(markets_to_create)} markets (total: {total_events[0]})")

    def _process_kalshi_event(
        self,
        event_data: dict,
        close_after_dt: Optional[datetime],
        events_batch: List[Event],
        market_data_batch: Dict[str, dict]
    ) -> bool:
        """Process a single Kalshi event and add to batch if it passes filters. Returns True if added."""
        # Debug: Save first 5 event_data samples
        if self._kalshi_events_saved < 5 and self.debug:
            kalshi_dir = os.path.join(self._debug_dir, 'kalshi')
            os.makedirs(kalshi_dir, exist_ok=True)
            filepath = os.path.join(kalshi_dir, f'event_{self._kalshi_events_saved}.json')
            with open(filepath, 'w') as f:
                json.dump(event_data, f, indent=2, default=str)
            self._kalshi_events_saved += 1

        event_ticker = event_data.get('event_ticker', '')

        if not event_ticker:
            return False

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

        # Client-side date filtering
        if close_after_dt and event_close_time:
            if event_close_time < close_after_dt:
                return False

        # Build URL
        url = f"https://kalshi.com/markets/{event_ticker}"
        # Calculate aggregated volume from markets
        total_volume = sum(m.get('volume', 0) or 0 for m in markets)
        total_volume_24h = sum(m.get('volume_24h', 0) or 0 for m in markets)
        total_liquidity = sum(m.get('liquidity', 0) or 0 for m in markets)
        total_open_interest = sum(m.get('open_interest', 0) or 0 for m in markets)

        # Create Event object
        events_batch.append(Event(
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
            end_date=event_close_time
        ))
        # Store market data
        market_data_batch[event_ticker] = {
            'markets': markets,
            'url': url
        }
        return True

    def sync_kalshi_events(
        self,
        close_after: Optional[str] = None
    ) -> List[Event]:
        """
        Sync events from Kalshi with their nested markets.
        Fetches and saves in batches to minimize memory usage.
        """
        total_events = [0]  # Use list to allow modification in nested function
        events_batch = []
        market_data_batch = {}
        seen_tickers = set()

        # Convert date strings to Unix timestamps for Kalshi API
        min_close_ts = None
        if close_after:
            try:
                dt = datetime.strptime(close_after, '%Y-%m-%d')
                min_close_ts = int(dt.timestamp())
            except ValueError:
                logger.warning(f"Invalid close_after date format: {close_after}")

        # Parse date filters for client-side filtering
        close_after_dt = None
        if close_after:
            try:
                close_after_dt = datetime.strptime(close_after, '%Y-%m-%d')
            except ValueError:
                pass

        try:
            # Fetch all regular events page by page
            cursor = None
            while True:
                response = self.kalshi_client.get_events(
                    status='open',
                    cursor=cursor,
                    with_nested_markets=True,
                    min_close_ts=min_close_ts
                )
                events = response.get('events', [])

                for event_data in events:
                    ticker = event_data.get('event_ticker', '')
                    if ticker and ticker not in seen_tickers:
                        seen_tickers.add(ticker)
                        self._process_kalshi_event(
                            event_data, close_after_dt,
                            events_batch, market_data_batch
                        )
                        # Flush if batch is full
                        if len(events_batch) >= BATCH_SIZE:
                            self._flush_kalshi_batch(events_batch, market_data_batch, total_events)
                            events_batch = []
                            market_data_batch = {}

                cursor = response.get('cursor')
                if not cursor or not events:
                    break

                logger.info(f"Fetched page of {len(events)} regular Kalshi events")

            # Fetch and process multivariate events page by page
            cursor = None
            while True:
                response = self.kalshi_client.get_multivariate_events(
                    cursor=cursor,
                    with_nested_markets=True
                )
                events = response.get('events', [])

                for event_data in events:
                    ticker = event_data.get('event_ticker', '')
                    if ticker and ticker not in seen_tickers:
                        seen_tickers.add(ticker)
                        self._process_kalshi_event(
                            event_data, close_after_dt,
                            events_batch, market_data_batch
                        )

                        # Flush if batch is full
                        if len(events_batch) >= BATCH_SIZE:
                            self._flush_kalshi_batch(events_batch, market_data_batch, total_events)
                            events_batch = []
                            market_data_batch = {}

                cursor = response.get('cursor')
                if not cursor or not events:
                    break

                logger.info(f"Fetched page of {len(events)} multivariate Kalshi events")

            # Flush any remaining events
            if events_batch:
                self._flush_kalshi_batch(events_batch, market_data_batch, total_events)

            logger.info(f"Synced {total_events[0]} Kalshi events total")

        except Exception as e:
            logger.error(f"Error syncing Kalshi events: {e}")
            raise

        # Return empty list (we track count, not actual objects to save memory)
        return [None] * total_events[0]  # Return placeholder list with correct count

    def _flush_polymarket_batch(
        self,
        events_batch: List[Event],
        market_data_batch: Dict[str, dict],
        total_events: List[int]
    ) -> None:
        """Flush a batch of Polymarket events and their markets to the database"""
        if not events_batch:
            return

        # Bulk create events and get their IDs
        event_ids = self._bulk_create_events(events_batch, Exchange.POLYMARKET)
        total_events[0] += len(events_batch)

        # Create markets for this batch
        markets_to_create = []
        for external_id, data in market_data_batch.items():
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

        # Bulk create markets
        self._bulk_create_markets(markets_to_create)
        logger.info(f"Flushed batch: {len(events_batch)} events, {len(markets_to_create)} markets (total: {total_events[0]})")

    def _process_polymarket_event(
        self,
        event_data: dict,
        events_batch: List[Event],
        market_data_batch: Dict[str, dict]
    ) -> bool:
        """Process a single Polymarket event and add to batch. Returns True if added."""
        # Debug: Save first 5 event_data samples
        if self._polymarket_events_saved < 5 and self.debug:
            poly_dir = os.path.join(self._debug_dir, 'polymarket')
            os.makedirs(poly_dir, exist_ok=True)
            filepath = os.path.join(poly_dir, f'event_{self._polymarket_events_saved}.json')
            with open(filepath, 'w') as f:
                json.dump(event_data, f, indent=2, default=str)
            self._polymarket_events_saved += 1

        event_id = event_data.get('id', '')
        slug = event_data.get('slug', '')
        if not event_id and not slug:
            return False

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

        # Create Event object
        events_batch.append(Event(
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

        # Store market data
        market_data_batch[external_id] = {
            'markets': event_data.get('markets', []),
            'slug': slug
        }

        return True

    def sync_polymarket_events(
        self,
        close_after: Optional[str] = None
    ) -> List[Event]:
        """
        Sync events from Polymarket with their nested markets.
        Fetches and saves in batches to minimize memory usage.
        """
        total_events = [0]  # Use list to allow modification in nested function
        events_batch = []
        market_data_batch = {}
        seen_ids = set()

        # Convert date strings to ISO 8601 format for Polymarket API
        end_date_min = None
        if close_after:
            try:
                dt = datetime.strptime(close_after, '%Y-%m-%d')
                end_date_min = dt.strftime('%Y-%m-%dT00:00:00.000Z')
            except ValueError:
                logger.warning(f"Invalid close_after date format: {close_after}")

        try:
            # Fetch all events page by page
            offset = 0
            limit = 200

            while True:
                try:
                    response = self.poly_client.get_events(
                        offset=offset,
                        limit=limit,
                        active=True,
                        end_date_min=end_date_min
                    )
                except Exception as e:
                    logger.error(f"Failed to fetch events at offset {offset}: {e}")
                    break

                if isinstance(response, list):
                    events = response
                elif isinstance(response, dict):
                    events = response.get('data', [])
                else:
                    events = []

                if not events:
                    break

                for event_data in events:
                    event_id = event_data.get('id', '')
                    if event_id and event_id not in seen_ids:
                        seen_ids.add(event_id)
                        self._process_polymarket_event(event_data, events_batch, market_data_batch)

                        # Flush if batch is full
                        if len(events_batch) >= BATCH_SIZE:
                            self._flush_polymarket_batch(events_batch, market_data_batch, total_events)
                            events_batch = []
                            market_data_batch = {}

                logger.info(f"Fetched page of {len(events)} Polymarket events (offset: {offset})")

                if len(events) < limit:
                    break

                offset += limit

            # Flush any remaining events
            if events_batch:
                self._flush_polymarket_batch(events_batch, market_data_batch, total_events)

            logger.info(f"Synced {total_events[0]} Polymarket events total")

        except Exception as e:
            logger.error(f"Error syncing Polymarket events: {e}")
            raise

        # Return placeholder list with correct count
        return [None] * total_events[0]

    def sync_all_events(
        self,
        close_after: Optional[str] = None
    ) -> Dict[str, List[Event]]:
        """Sync events from all exchanges in parallel, with optional close_after filtering"""
        results = {
            'kalshi': [],
            'polymarket': []
        }

        # Run both syncs in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(
                    self.sync_kalshi_events,
                    close_after
                ): 'kalshi',
                executor.submit(
                    self.sync_polymarket_events,
                    close_after
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
