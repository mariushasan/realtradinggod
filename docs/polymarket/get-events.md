# Polymarket: Get Events

Retrieve a paginated list of events. Events group related markets together.

## Endpoint

```
GET https://gamma-api.polymarket.com/events
```

## Authentication

Not required.

## Query Parameters

### Pagination & Sorting

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | - | Results per page (≥0) |
| `offset` | integer | No | 0 | Number of results to skip |
| `order` | string | No | - | Comma-separated fields to order by |
| `ascending` | boolean | No | false | Sort direction |

### Filtering

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer[] | No | Filter by event IDs |
| `slug` | string[] | No | Filter by event slugs |
| `tag_id` | integer | No | Filter by tag ID |
| `tag_slug` | string | No | Filter by tag slug |
| `exclude_tag_id` | integer[] | No | Exclude events with these tag IDs |
| `active` | boolean | No | Filter by active status |
| `closed` | boolean | No | Filter by closed status |
| `archived` | boolean | No | Filter by archived status |
| `featured` | boolean | No | Filter featured events |
| `cyom` | boolean | No | Filter Create Your Own Market events |

### Volume & Liquidity

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `liquidity_min` | number | No | Minimum liquidity |
| `liquidity_max` | number | No | Maximum liquidity |
| `volume_min` | number | No | Minimum volume |
| `volume_max` | number | No | Maximum volume |

### Date Filters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date_min` | datetime | No | Minimum start date (ISO 8601) |
| `start_date_max` | datetime | No | Maximum start date (ISO 8601) |
| `end_date_min` | datetime | No | Minimum end date (ISO 8601) |
| `end_date_max` | datetime | No | Maximum end date (ISO 8601) |

### Options

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `related_tags` | boolean | No | Include related tags |
| `include_chat` | boolean | No | Include chat information |
| `include_template` | boolean | No | Include template data |
| `recurrence` | string | No | Filter by recurrence pattern |

## Example Request

```bash
curl "https://gamma-api.polymarket.com/events?limit=10&active=true&order=volume&ascending=false"
```

## Response

```json
[
  {
    "id": "67890",
    "ticker": "BTC-2024",
    "slug": "bitcoin-price-predictions-2024",
    "title": "Bitcoin Price Predictions 2024",
    "subtitle": "Where will Bitcoin's price be?",
    "description": "A collection of markets predicting Bitcoin's price movements in 2024.",
    "resolutionSource": "https://coinmarketcap.com/currencies/bitcoin/",
    "startDate": "2024-01-01T00:00:00.000Z",
    "endDate": "2024-12-31T23:59:59.000Z",
    "image": "https://polymarket.com/images/btc-2024.png",
    "active": true,
    "closed": false,
    "featured": true,
    "liquidity": 500000,
    "volume": 2500000,
    "volume24hr": 75000,
    "negRisk": true,
    "negRiskMarketID": "0xabc123...",
    "markets": [
      {
        "id": "12345",
        "question": "Will Bitcoin reach $100,000?",
        "outcomePrices": "[\"0.45\", \"0.55\"]"
      }
    ],
    "tags": [
      {
        "id": "1",
        "label": "Crypto",
        "slug": "crypto"
      }
    ]
  }
]
```

## Response Fields

### Event Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique event identifier |
| `ticker` | string | Event ticker symbol |
| `slug` | string | URL-friendly identifier |
| `title` | string | Event title |
| `subtitle` | string | Event subtitle |
| `description` | string | Full event description |
| `resolutionSource` | string | Source URL for resolution |
| `image` | string | Event image URL |
| `icon` | string | Event icon URL |

### Status Fields

| Field | Type | Description |
|-------|------|-------------|
| `active` | boolean | Event is active |
| `closed` | boolean | Event has ended |
| `archived` | boolean | Event is archived |
| `featured` | boolean | Event is featured |
| `new` | boolean | Event is new |

### Trading Fields

| Field | Type | Description |
|-------|------|-------------|
| `liquidity` | number | Total liquidity across markets |
| `volume` | number | Total trading volume |
| `openInterest` | number | Open interest |
| `enableOrderBook` | boolean | CLOB trading available |

### Negative Risk Fields

| Field | Type | Description |
|-------|------|-------------|
| `negRisk` | boolean | Event uses negative risk model |
| `negRiskMarketID` | string | Neg-risk market contract ID |
| `negRiskFeeBips` | integer | Fee in basis points |

### Volume Metrics

| Field | Type | Description |
|-------|------|-------------|
| `volume24hr` | number | 24-hour volume |
| `volume1wk` | number | Weekly volume |
| `volume1mo` | number | Monthly volume |
| `volume1yr` | number | Yearly volume |

### Timestamps

| Field | Type | Description |
|-------|------|-------------|
| `startDate` | string | Event start (ISO 8601) |
| `endDate` | string | Event end (ISO 8601) |
| `createdAt` | string | Creation timestamp |
| `updatedAt` | string | Last update timestamp |

### Nested Objects

| Field | Type | Description |
|-------|------|-------------|
| `markets` | array | Markets within this event |
| `tags` | array | Associated tags |
| `categories` | array | Event categories |
| `series` | array | Related series |
| `collections` | array | Collections containing this event |

## Notes

- Events can contain multiple markets
- `negRisk` events have special pricing mechanics for mutually exclusive outcomes
- Use nested `markets` array to get market data in one request
- Returns an array (not wrapped in object)
