# Kalshi: Get Event by Ticker

Retrieve detailed information about a specific event and its markets.

## Endpoint

```
GET https://api.elections.kalshi.com/trade-api/v2/events/{event_ticker}
```

## Authentication

Not required for public event data.

## Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_ticker` | string | Yes | Event ticker (e.g., `INXD-24DEC31`) |

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `with_nested_markets` | boolean | No | false | If true, markets are nested inside the event object |

## Example Request

```bash
# Get event with nested markets
curl "https://api.elections.kalshi.com/trade-api/v2/events/INXD-24DEC31?with_nested_markets=true"
```

## Response

```json
{
  "event": {
    "event_ticker": "INXD-24DEC31",
    "series_ticker": "INXD",
    "title": "S&P 500 End of Day Dec 31, 2024",
    "sub_title": "Where will the S&P 500 close?",
    "category": "Economics",
    "status": "open",
    "mutually_exclusive": true,
    "strike_date": "2024-12-31",
    "markets": [
      {
        "ticker": "INXD-24DEC31-B4903",
        "title": "S&P 500 to close at 4,903 or above?",
        "status": "open",
        "yes_bid": 45,
        "yes_ask": 47,
        "volume": 12500
      }
    ]
  },
  "markets": [
    {
      "ticker": "INXD-24DEC31-B4903",
      "title": "S&P 500 to close at 4,903 or above?",
      "status": "open",
      "yes_bid": 45,
      "yes_ask": 47,
      "volume": 12500
    }
  ]
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `event` | object | Event object with details |
| `markets` | array | Markets in this event (top-level, deprecated) |

### Event Object

| Field | Type | Description |
|-------|------|-------------|
| `event_ticker` | string | Unique event identifier |
| `series_ticker` | string | Parent series identifier |
| `title` | string | Event title |
| `sub_title` | string | Event subtitle/description |
| `category` | string | Event category |
| `status` | string | Current status: `open`, `closed`, `settled` |
| `mutually_exclusive` | boolean | Whether markets are mutually exclusive |
| `strike_date` | string | Date the event resolves (YYYY-MM-DD) |
| `markets` | array | Nested markets (if `with_nested_markets=true`) |

## Notes

- The top-level `markets` field is deprecated
- Use `with_nested_markets=true` to get markets nested inside the event object
- Events contain one or more markets representing different outcomes
- For mutually exclusive events, exactly one market will settle YES
