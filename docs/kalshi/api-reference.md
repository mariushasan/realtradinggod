# Kalshi API Reference

Complete reference for the Kalshi Trade API v2.

## Base URL

```
https://api.elections.kalshi.com/trade-api/v2
```

## Authentication

Public endpoints (markets, events) do not require authentication. Trading endpoints require API key authentication.

### API Key Headers

```
KALSHI-ACCESS-KEY: your-api-key
KALSHI-ACCESS-SIGNATURE: signature
KALSHI-ACCESS-TIMESTAMP: unix-timestamp
```

## Rate Limits

- Market data: 10 requests/second
- Trading: 20 orders/second

## Endpoints Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/markets` | GET | No | List markets |
| `/markets/{ticker}` | GET | No | Get market details |
| `/events` | GET | No | List events |
| `/events/{event_ticker}` | GET | No | Get event details |
| `/search/tags_by_categories` | GET | No | Get tags |

## Common Response Patterns

### Pagination

Kalshi uses cursor-based pagination:

```json
{
  "data": [...],
  "cursor": "eyJsYXN0X2lkIjo..."
}
```

To get the next page, pass the cursor:
```
GET /markets?cursor=eyJsYXN0X2lkIjo...
```

### Error Response

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Market not found"
  }
}
```

## Data Types

### Market Status

| Status | Description |
|--------|-------------|
| `unopened` | Market created but not yet open for trading |
| `open` | Market is open for trading |
| `closed` | Trading has ended, awaiting settlement |
| `settled` | Market has been settled with a result |

### Price Format

- Prices are in **cents** (1-99)
- YES price + NO price ≈ 100
- Example: YES at 45¢ means 45% implied probability

### Timestamps

- All timestamps are Unix timestamps (seconds since epoch)
- ISO 8601 format used in some response fields

## Common Query Patterns

### Get all open markets for an event

```bash
curl "https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker=INXD-24DEC31&status=open"
```

### Get events with markets in one request

```bash
curl "https://api.elections.kalshi.com/trade-api/v2/events?status=open&with_nested_markets=true"
```

### Filter by time range

```bash
curl "https://api.elections.kalshi.com/trade-api/v2/markets?min_close_ts=1704067200&max_close_ts=1706745600"
```

## OpenAPI Specification

See `kalshiopenapi.yaml` for the complete OpenAPI 3.0 specification.
