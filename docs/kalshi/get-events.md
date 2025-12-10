# Kalshi: Get Events

Retrieve a paginated list of events. Events are containers for related markets.

## Endpoint

```
GET https://api.elections.kalshi.com/trade-api/v2/events
```

## Authentication

Not required for public event data.

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 200 | Results per page (1-200) |
| `cursor` | string | No | - | Pagination cursor from previous response |
| `status` | string | No | - | Filter by status: `open`, `closed`, `settled` |
| `series_ticker` | string | No | - | Filter by series ticker |
| `with_nested_markets` | boolean | No | false | Include nested market objects |
| `with_milestones` | boolean | No | false | Include related milestones |
| `min_close_ts` | integer | No | - | Filter events with markets closing after this Unix timestamp |

## Example Request

```bash
# Get open events with nested markets
curl "https://api.elections.kalshi.com/trade-api/v2/events?status=open&with_nested_markets=true&limit=10"
```

## Response

```json
{
  "events": [
    {
      "event_ticker": "INXD-24DEC31",
      "series_ticker": "INXD",
      "title": "S&P 500 End of Day Dec 31, 2024",
      "category": "Economics",
      "sub_title": "Where will the S&P 500 close?",
      "status": "open",
      "mutually_exclusive": true,
      "markets": [
        {
          "ticker": "INXD-24DEC31-B4903",
          "title": "S&P 500 to close at 4,903 or above?",
          "status": "open",
          "yes_bid": 45,
          "yes_ask": 47
        }
      ]
    }
  ],
  "cursor": "eyJsYXN0X2lkIjo...",
  "milestones": []
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `events` | array | Array of event objects |
| `cursor` | string | Pagination cursor for next page (empty if no more results) |
| `milestones` | array | Related milestones (if `with_milestones=true`) |

### Event Object

| Field | Type | Description |
|-------|------|-------------|
| `event_ticker` | string | Unique event identifier |
| `series_ticker` | string | Parent series identifier |
| `title` | string | Event title |
| `sub_title` | string | Event subtitle/description |
| `category` | string | Event category (e.g., "Economics", "Politics") |
| `status` | string | Current status: `open`, `closed`, `settled` |
| `mutually_exclusive` | boolean | Whether markets within event are mutually exclusive |
| `markets` | array | Nested markets (if `with_nested_markets=true`) |

## Notes

- This endpoint excludes multivariate events by default
- For multivariate events, use `GET /events/multivariate`
- Use `with_nested_markets=true` to get markets in a single request
- Maximum 200 results per page (lower than markets endpoint)
