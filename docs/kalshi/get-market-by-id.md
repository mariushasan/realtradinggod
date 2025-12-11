# Kalshi: Get Market by Ticker

Retrieve detailed information about a specific market by its ticker.

## Endpoint

```
GET https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}
```

## Authentication

Not required for public market data.

## Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | Yes | Market ticker (e.g., `INXD-24DEC31-B4903`) |

## Example Request

```bash
curl "https://api.elections.kalshi.com/trade-api/v2/markets/INXD-24DEC31-B4903"
```

## Response

```json
{
  "market": {
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
}
```

## Response Fields

### Market Object

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Unique market identifier |
| `event_ticker` | string | Parent event identifier |
| `series_ticker` | string | Series identifier |
| `title` | string | Market question/title |
| `subtitle` | string | Additional context |
| `status` | string | Current status: `unopened`, `open`, `closed`, `settled` |
| `yes_bid` | integer | Best bid price for YES (cents) |
| `yes_ask` | integer | Best ask price for YES (cents) |
| `no_bid` | integer | Best bid price for NO (cents) |
| `no_ask` | integer | Best ask price for NO (cents) |
| `last_price` | integer | Last traded price (cents) |
| `volume` | integer | Total contracts traded (all time) |
| `volume_24h` | integer | Contracts traded in last 24 hours |
| `open_interest` | integer | Outstanding contracts |
| `open_time` | string | ISO 8601 timestamp when market opened |
| `close_time` | string | ISO 8601 timestamp when trading closes |
| `expiration_time` | string | ISO 8601 timestamp when market settles |
| `result` | string | Settlement result: `yes`, `no`, or `null` |
| `can_close_early` | boolean | Whether market can settle before close time |
| `floor_strike` | number | Lower bound strike price (if applicable) |
| `cap_strike` | number | Upper bound strike price (if applicable) |
| `rules_primary` | string | Primary resolution rules |
| `rules_secondary` | string | Secondary resolution details |

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 404 | Market not found |
| 500 | Internal server error |

## Notes

- Market tickers follow the format: `{SERIES}-{EXPIRY}-{STRIKE}`
- Example ticker breakdown: `INXD-24DEC31-B4903`
  - `INXD` = S&P 500 Index series
  - `24DEC31` = December 31, 2024 expiry
  - `B4903` = Above 4903 strike
