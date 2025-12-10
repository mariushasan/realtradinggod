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
      "ticker": "INXD-24DEC31-B4903",
      "event_ticker": "INXD-24DEC31",
      "title": "S&P 500 to close at 4,903 or above on Dec 31?",
      "subtitle": "S&P 500 End of Day",
      "status": "open",
      "yes_bid": 45,
      "yes_ask": 47,
      "no_bid": 53,
      "no_ask": 55,
      "volume": 12500,
      "open_interest": 8200,
      "close_time": "2024-12-31T21:00:00Z",
      "result": null
    }
  ],
  "cursor": "eyJsYXN0X2lkIjo..."
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
