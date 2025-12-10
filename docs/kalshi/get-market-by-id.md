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
    "ticker": "INXD-24DEC31-B4903",
    "event_ticker": "INXD-24DEC31",
    "series_ticker": "INXD",
    "title": "S&P 500 to close at 4,903 or above on Dec 31?",
    "subtitle": "S&P 500 End of Day",
    "status": "open",
    "yes_bid": 45,
    "yes_ask": 47,
    "no_bid": 53,
    "no_ask": 55,
    "last_price": 46,
    "volume": 12500,
    "volume_24h": 1250,
    "open_interest": 8200,
    "open_time": "2024-01-01T00:00:00Z",
    "close_time": "2024-12-31T21:00:00Z",
    "expiration_time": "2024-12-31T21:00:00Z",
    "result": null,
    "can_close_early": false,
    "floor_strike": 4903,
    "cap_strike": null,
    "rules_primary": "This market will resolve to Yes if...",
    "rules_secondary": "Settlement will be based on..."
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
