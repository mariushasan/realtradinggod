# Polymarket: Get Market by ID

Retrieve detailed information about a specific market by its ID.

## Endpoint

```
GET https://gamma-api.polymarket.com/markets/{id}
```

## Authentication

Not required.

## Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Market ID |

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_tag` | boolean | No | false | Include tag objects in response |

## Example Request

```bash
curl "https://gamma-api.polymarket.com/markets/12345"
```

## Response

```json
{
  "id": "12345",
  "question": "Will Bitcoin reach $100,000 by end of 2024?",
  "conditionId": "0x1234567890abcdef...",
  "slug": "will-bitcoin-reach-100000",
  "description": "This market resolves to Yes if Bitcoin's price reaches or exceeds $100,000 USD at any point before December 31, 2024 23:59:59 UTC.",
  "resolutionSource": "https://coinmarketcap.com/currencies/bitcoin/",
  "outcomes": "[\"Yes\", \"No\"]",
  "outcomePrices": "[\"0.45\", \"0.55\"]",
  "volume": "1500000",
  "volumeNum": 1500000,
  "liquidity": "250000",
  "liquidityNum": 250000,
  "startDate": "2024-01-01T00:00:00.000Z",
  "endDate": "2024-12-31T23:59:59.000Z",
  "createdAt": "2024-01-01T00:00:00.000Z",
  "updatedAt": "2024-06-15T12:30:00.000Z",
  "active": true,
  "closed": false,
  "archived": false,
  "featured": true,
  "enableOrderBook": true,
  "clobTokenIds": "[\"71321\", \"71322\"]",
  "marketMakerAddress": "0xabcdef1234567890...",
  "bestBid": 0.44,
  "bestAsk": 0.46,
  "lastTradePrice": 0.45,
  "spread": 0.02,
  "volume24hr": 50000,
  "volume1wk": 200000,
  "volume1mo": 750000,
  "oneDayPriceChange": 0.02,
  "oneWeekPriceChange": 0.05,
  "oneMonthPriceChange": 0.10,
  "events": [
    {
      "id": "67890",
      "title": "Bitcoin Price Predictions 2024"
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
```

## Response Fields

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique market identifier |
| `question` | string | Market question |
| `conditionId` | string | Gnosis condition ID for on-chain trading |
| `slug` | string | URL-friendly identifier |
| `description` | string | Full market description and rules |
| `resolutionSource` | string | Source URL for resolution |
| `outcomes` | string | JSON array of outcome names |
| `outcomePrices` | string | JSON array of current prices (decimal) |

### Status Fields

| Field | Type | Description |
|-------|------|-------------|
| `active` | boolean | Market is active for trading |
| `closed` | boolean | Trading has ended |
| `archived` | boolean | Market is archived |
| `featured` | boolean | Market is featured on homepage |

### Trading Fields

| Field | Type | Description |
|-------|------|-------------|
| `enableOrderBook` | boolean | CLOB trading available |
| `clobTokenIds` | string | JSON array of token IDs for CLOB |
| `marketMakerAddress` | string | AMM contract address |
| `bestBid` | number | Current best bid |
| `bestAsk` | number | Current best ask |
| `lastTradePrice` | number | Most recent trade price |
| `spread` | number | Bid-ask spread |

### Volume & Liquidity

| Field | Type | Description |
|-------|------|-------------|
| `volume` / `volumeNum` | string/number | Total volume |
| `liquidity` / `liquidityNum` | string/number | Current liquidity |
| `volume24hr` | number | 24-hour volume |
| `volume1wk` | number | Weekly volume |
| `volume1mo` | number | Monthly volume |

### Price Changes

| Field | Type | Description |
|-------|------|-------------|
| `oneDayPriceChange` | number | 24-hour price change |
| `oneWeekPriceChange` | number | 7-day price change |
| `oneMonthPriceChange` | number | 30-day price change |

### Timestamps

| Field | Type | Description |
|-------|------|-------------|
| `startDate` | string | When market starts (ISO 8601) |
| `endDate` | string | When market ends (ISO 8601) |
| `createdAt` | string | Creation timestamp |
| `updatedAt` | string | Last update timestamp |

### Related Objects

| Field | Type | Description |
|-------|------|-------------|
| `events` | array | Parent events containing this market |
| `tags` | array | Associated tags |
| `categories` | array | Market categories |

## Notes

- Use `conditionId` for on-chain operations
- Use `clobTokenIds` for CLOB API trading
- Prices are in decimal format (0.01-0.99)
- `outcomes` and `outcomePrices` are JSON strings that need parsing
