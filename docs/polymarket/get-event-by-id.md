# Polymarket: Get Event by ID

Retrieve detailed information about a specific event and its markets.

## Endpoint

```
GET https://gamma-api.polymarket.com/events/{id}
```

## Authentication

Not required.

## Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Event ID |

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_chat` | boolean | No | false | Include chat information |
| `include_template` | boolean | No | false | Include template data |

## Example Request

```bash
curl "https://gamma-api.polymarket.com/events/67890"
```

## Response

```json
{
  "id": "67890",
  "ticker": "BTC-2024",
  "slug": "bitcoin-price-predictions-2024",
  "title": "Bitcoin Price Predictions 2024",
  "subtitle": "Where will Bitcoin's price be?",
  "description": "A collection of markets predicting Bitcoin's price movements in 2024. Markets will resolve based on the official Bitcoin price from CoinMarketCap.",
  "resolutionSource": "https://coinmarketcap.com/currencies/bitcoin/",
  "startDate": "2024-01-01T00:00:00.000Z",
  "creationDate": "2023-12-15T00:00:00.000Z",
  "endDate": "2024-12-31T23:59:59.000Z",
  "image": "https://polymarket.com/images/btc-2024.png",
  "icon": "https://polymarket.com/icons/btc.png",
  "active": true,
  "closed": false,
  "archived": false,
  "featured": true,
  "restricted": false,
  "liquidity": 500000,
  "volume": 2500000,
  "openInterest": 150000,
  "category": "Crypto",
  "subcategory": "Bitcoin",
  "enableOrderBook": true,
  "negRisk": true,
  "negRiskMarketID": "0xabc123def456...",
  "negRiskFeeBips": 100,
  "volume24hr": 75000,
  "volume1wk": 300000,
  "volume1mo": 1200000,
  "competitive": 0.85,
  "commentCount": 245,
  "commentsEnabled": true,
  "markets": [
    {
      "id": "12345",
      "question": "Will Bitcoin reach $100,000 by end of 2024?",
      "conditionId": "0x1234567890abcdef...",
      "outcomes": "[\"Yes\", \"No\"]",
      "outcomePrices": "[\"0.45\", \"0.55\"]",
      "volume": "750000",
      "clobTokenIds": "[\"71321\", \"71322\"]"
    },
    {
      "id": "12346",
      "question": "Will Bitcoin drop below $30,000 in 2024?",
      "conditionId": "0xfedcba0987654321...",
      "outcomes": "[\"Yes\", \"No\"]",
      "outcomePrices": "[\"0.15\", \"0.85\"]",
      "volume": "500000",
      "clobTokenIds": "[\"71323\", \"71324\"]"
    }
  ],
  "tags": [
    {
      "id": "1",
      "label": "Crypto",
      "slug": "crypto"
    },
    {
      "id": "15",
      "label": "Bitcoin",
      "slug": "bitcoin"
    }
  ],
  "categories": [
    {
      "id": "5",
      "name": "Cryptocurrency"
    }
  ],
  "series": [],
  "collections": []
}
```

## Response Fields

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique event identifier |
| `ticker` | string | Event ticker symbol |
| `slug` | string | URL-friendly identifier |
| `title` | string | Event title |
| `subtitle` | string | Event subtitle |
| `description` | string | Full event description |
| `resolutionSource` | string | Resolution source URL |
| `category` | string | Primary category |
| `subcategory` | string | Sub-category |

### Media Fields

| Field | Type | Description |
|-------|------|-------------|
| `image` | string | Event image URL |
| `icon` | string | Event icon URL |
| `featuredImage` | string | Featured image URL |

### Status Fields

| Field | Type | Description |
|-------|------|-------------|
| `active` | boolean | Event is active |
| `closed` | boolean | Event has ended |
| `archived` | boolean | Event is archived |
| `featured` | boolean | Event is featured |
| `restricted` | boolean | Event has restrictions |

### Trading Metrics

| Field | Type | Description |
|-------|------|-------------|
| `liquidity` | number | Total liquidity |
| `volume` | number | Total volume |
| `openInterest` | number | Open interest |
| `competitive` | number | Competitiveness score (0-1) |

### Negative Risk

| Field | Type | Description |
|-------|------|-------------|
| `negRisk` | boolean | Uses negative risk model |
| `negRiskMarketID` | string | Neg-risk contract ID |
| `negRiskFeeBips` | integer | Fee in basis points (100 = 1%) |
| `enableNegRisk` | boolean | Neg-risk is enabled |

### Volume History

| Field | Type | Description |
|-------|------|-------------|
| `volume24hr` | number | 24-hour volume |
| `volume1wk` | number | 7-day volume |
| `volume1mo` | number | 30-day volume |
| `volume1yr` | number | 1-year volume |

### Social/Community

| Field | Type | Description |
|-------|------|-------------|
| `commentCount` | integer | Number of comments |
| `commentsEnabled` | boolean | Comments are enabled |
| `tweetCount` | integer | Related tweets |

### Timestamps

| Field | Type | Description |
|-------|------|-------------|
| `startDate` | string | Event start (ISO 8601) |
| `endDate` | string | Event end (ISO 8601) |
| `creationDate` | string | Creation timestamp |
| `createdAt` | string | DB creation timestamp |
| `updatedAt` | string | Last update timestamp |

### Nested Objects

| Field | Type | Description |
|-------|------|-------------|
| `markets` | array | Markets in this event |
| `tags` | array | Associated tags |
| `categories` | array | Event categories |
| `series` | array | Related series |
| `collections` | array | Parent collections |

## Notes

- Events group related markets together (e.g., all Bitcoin price predictions)
- `negRisk` events have mutually exclusive outcomes across markets
- Use markets array to get all tradeable outcomes
- Each market has its own `conditionId` and `clobTokenIds` for trading
