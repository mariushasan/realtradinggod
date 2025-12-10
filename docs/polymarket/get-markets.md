# Polymarket: Get Markets

Retrieve a paginated list of markets with various filtering and sorting options.

## Endpoint

```
GET https://gamma-api.polymarket.com/markets
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
| `id` | integer[] | No | Filter by market IDs |
| `slug` | string[] | No | Filter by market slugs |
| `clob_token_ids` | string[] | No | Filter by CLOB token IDs |
| `condition_ids` | string[] | No | Filter by condition IDs |
| `question_ids` | string[] | No | Filter by question IDs |
| `tag_id` | integer | No | Filter by tag ID |
| `closed` | boolean | No | Filter by closed status |

### Volume & Liquidity Filters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `liquidity_num_min` | number | No | Minimum liquidity |
| `liquidity_num_max` | number | No | Maximum liquidity |
| `volume_num_min` | number | No | Minimum volume |
| `volume_num_max` | number | No | Maximum volume |

### Date Filters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date_min` | datetime | No | Minimum start date (ISO 8601) |
| `start_date_max` | datetime | No | Maximum start date (ISO 8601) |
| `end_date_min` | datetime | No | Minimum end date (ISO 8601) |
| `end_date_max` | datetime | No | Maximum end date (ISO 8601) |

### Other Filters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `related_tags` | boolean | No | Include related tags |
| `include_tag` | boolean | No | Include tag objects in response |
| `cyom` | boolean | No | Filter Create Your Own Market |
| `game_id` | string | No | Filter by game ID |
| `sports_market_types` | string[] | No | Filter by sports market types |
| `rewards_min_size` | number | No | Minimum rewards size |

## Example Request

```bash
curl "https://gamma-api.polymarket.com/markets?limit=10&closed=false&order=volume&ascending=false"
```

## Response

```json
[
  {
    "id": "12345",
    "question": "Will Bitcoin reach $100,000 by end of 2024?",
    "conditionId": "0x1234567890abcdef...",
    "slug": "will-bitcoin-reach-100000",
    "description": "This market resolves to Yes if...",
    "outcomes": "[\"Yes\", \"No\"]",
    "outcomePrices": "[\"0.45\", \"0.55\"]",
    "volume": "1500000",
    "volumeNum": 1500000,
    "liquidity": "250000",
    "liquidityNum": 250000,
    "startDate": "2024-01-01T00:00:00.000Z",
    "endDate": "2024-12-31T23:59:59.000Z",
    "active": true,
    "closed": false,
    "enableOrderBook": true,
    "clobTokenIds": "[\"71321\", \"71322\"]",
    "bestBid": 0.44,
    "bestAsk": 0.46,
    "lastTradePrice": 0.45,
    "volume24hr": 50000,
    "oneDayPriceChange": 0.02
  }
]
```

## Response Fields

### Market Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique market identifier |
| `question` | string | Market question |
| `conditionId` | string | Gnosis condition ID |
| `slug` | string | URL-friendly identifier |
| `description` | string | Full market description |
| `outcomes` | string | JSON array of outcome names |
| `outcomePrices` | string | JSON array of outcome prices (decimal) |
| `volume` | string | Total volume traded (string) |
| `volumeNum` | number | Total volume traded (number) |
| `liquidity` | string | Current liquidity (string) |
| `liquidityNum` | number | Current liquidity (number) |
| `startDate` | string | ISO 8601 market start date |
| `endDate` | string | ISO 8601 market end date |
| `active` | boolean | Whether market is active |
| `closed` | boolean | Whether market is closed |
| `enableOrderBook` | boolean | Whether CLOB trading is enabled |
| `clobTokenIds` | string | JSON array of CLOB token IDs |
| `bestBid` | number | Current best bid price |
| `bestAsk` | number | Current best ask price |
| `lastTradePrice` | number | Most recent trade price |
| `volume24hr` | number | 24-hour trading volume |
| `oneDayPriceChange` | number | Price change in last 24 hours |

### Volume Fields

| Field | Description |
|-------|-------------|
| `volume24hr` | Volume in last 24 hours |
| `volume1wk` | Volume in last week |
| `volume1mo` | Volume in last month |
| `volume1yr` | Volume in last year |
| `volumeAmm` | Volume from AMM |
| `volumeClob` | Volume from CLOB |

## Notes

- Prices are in decimal format (0.01-0.99)
- Markets can be traded via CLOB if `enableOrderBook` is true
- Use `clobTokenIds` for trading via the CLOB API
- Returns an array (not wrapped in object like Kalshi)
- Volume/liquidity fields have both string and number versions
