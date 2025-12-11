# Kalshi: Get Markets

Retrieve a paginated list of markets with various filtering options.

## Endpoint

```
GET https://api.elections.kalshi.com/trade-api/v2/markets
```

## Authentication

Not required for public market data.

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 100 | Results per page (1-1000) |
| `cursor` | string | No | - | Pagination cursor from previous response |
| `event_ticker` | string | No | - | Filter by event ticker (comma-separated, max 10) |
| `series_ticker` | string | No | - | Filter by series ticker |
| `tickers` | string | No | - | Filter by market tickers (comma-separated) |
| `status` | string | No | - | Filter by status: `unopened`, `open`, `closed`, `settled` |
| `mve_filter` | string | No | - | Filter multivariate events: `only` or `exclude` |
| `min_created_ts` | integer | No | - | Filter markets created after this Unix timestamp |
| `max_created_ts` | integer | No | - | Filter markets created before this Unix timestamp |
| `min_close_ts` | integer | No | - | Filter markets closing after this Unix timestamp |
| `max_close_ts` | integer | No | - | Filter markets closing before this Unix timestamp |
| `min_settled_ts` | integer | No | - | Filter markets settled after this Unix timestamp |
| `max_settled_ts` | integer | No | - | Filter markets settled before this Unix timestamp |

### Timestamp Filter Compatibility

| Timestamp Filters | Compatible Status Filters |
|-------------------|--------------------------|
| `min_created_ts`, `max_created_ts` | `unopened`, `open`, or empty |
| `min_close_ts`, `max_close_ts` | `closed` or empty |
| `min_settled_ts`, `max_settled_ts` | `settled` or empty |

## Example Request

```bash
curl "https://api.elections.kalshi.com/trade-api/v2/markets?limit=10&status=open"
```

## Response

```json
{
  "markets": [
    {
      "ticker": "<string>",
      "event_ticker": "<string>",
      "market_type": "binary",
      "title": "<string>",
      "subtitle": "<string>",
      "yes_sub_title": "<string>",
      "no_sub_title": "<string>",
      "created_time": "2023-11-07T05:31:56Z",
      "open_time": "2023-11-07T05:31:56Z",
      "close_time": "2023-11-07T05:31:56Z",
      "expiration_time": "2023-11-07T05:31:56Z",
      "latest_expiration_time": "2023-11-07T05:31:56Z",
      "settlement_timer_seconds": 123,
      "status": "initialized",
      "response_price_units": "usd_cent",
      "yes_bid": 123,
      "yes_bid_dollars": "0.5600",
      "yes_ask": 123,
      "yes_ask_dollars": "0.5600",
      "no_bid": 123,
      "no_bid_dollars": "0.5600",
      "no_ask": 123,
      "no_ask_dollars": "0.5600",
      "last_price": 123,
      "last_price_dollars": "0.5600",
      "volume": 123,
      "volume_24h": 123,
      "result": "yes",
      "can_close_early": true,
      "open_interest": 123,
      "notional_value": 123,
      "notional_value_dollars": "0.5600",
      "previous_yes_bid": 123,
      "previous_yes_bid_dollars": "0.5600",
      "previous_yes_ask": 123,
      "previous_yes_ask_dollars": "0.5600",
      "previous_price": 123,
      "previous_price_dollars": "0.5600",
      "liquidity": 123,
      "liquidity_dollars": "0.5600",
      "expiration_value": "<string>",
      "category": "<string>",
      "risk_limit_cents": 123,
      "tick_size": 123,
      "rules_primary": "<string>",
      "rules_secondary": "<string>",
      "price_level_structure": "<string>",
      "price_ranges": [
        {
          "start": "<string>",
          "end": "<string>",
          "step": "<string>"
        }
      ],
      "expected_expiration_time": "2023-11-07T05:31:56Z",
      "settlement_value": 123,
      "settlement_value_dollars": "0.5600",
      "fee_waiver_expiration_time": "2023-11-07T05:31:56Z",
      "early_close_condition": "<string>",
      "strike_type": "greater",
      "floor_strike": 123,
      "cap_strike": 123,
      "functional_strike": "<string>",
      "custom_strike": {},
      "mve_collection_ticker": "<string>",
      "mve_selected_legs": [
        {
          "event_ticker": "<string>",
          "market_ticker": "<string>",
          "side": "<string>"
        }
      ],
      "primary_participant_key": "<string>"
    }
  ],
  "cursor": "<string>"
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `markets` | array | Array of market objects |
| `cursor` | string | Pagination cursor for next page (empty if no more results) |

### Market Object

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Unique market identifier |
| `event_ticker` | string | Parent event identifier |
| `title` | string | Market question/title |
| `subtitle` | string | Additional context |
| `status` | string | Current status: `unopened`, `open`, `closed`, `settled` |
| `yes_bid` | integer | Best bid price for YES (cents, 1-99) |
| `yes_ask` | integer | Best ask price for YES (cents, 1-99) |
| `no_bid` | integer | Best bid price for NO (cents, 1-99) |
| `no_ask` | integer | Best ask price for NO (cents, 1-99) |
| `volume` | integer | Total contracts traded |
| `open_interest` | integer | Outstanding contracts |
| `close_time` | string | ISO 8601 timestamp when market closes |
| `result` | string | Settlement result: `yes`, `no`, or `null` if not settled |

## Notes

- Prices are in cents (1-99 range)
- YES price + NO price should approximately equal 100 cents
- Only one timestamp filter pair can be used at a time
- Use cursor-based pagination for large result sets
