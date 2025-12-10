# Polymarket API Reference

Complete reference for the Polymarket Gamma API.

## Base URL

```
https://gamma-api.polymarket.com
```

## Authentication

The Gamma API is read-only and does not require authentication for public data.

For trading, use the CLOB API (separate documentation).

## Rate Limits

No documented rate limits, but please be respectful of the API.

## Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/markets` | GET | List markets |
| `/markets/{id}` | GET | Get market details |
| `/events` | GET | List events |
| `/events/{id}` | GET | Get event details |
| `/tags` | GET | List tags |

## Common Response Patterns

### Pagination

Polymarket uses offset-based pagination:

```bash
# First page
curl "https://gamma-api.polymarket.com/markets?limit=10&offset=0"

# Second page
curl "https://gamma-api.polymarket.com/markets?limit=10&offset=10"
```

### Sorting

```bash
# Sort by volume descending
curl "https://gamma-api.polymarket.com/markets?order=volumeNum&ascending=false"
```

### Response Format

All list endpoints return arrays directly (not wrapped in objects):

```json
[
  { "id": "1", ... },
  { "id": "2", ... }
]
```

## Data Types

### Market Status

| Field | Values | Description |
|-------|--------|-------------|
| `active` | true/false | Market is active for trading |
| `closed` | true/false | Trading has ended |
| `archived` | true/false | Market is archived |

### Price Format

- Prices are in **decimal** format (0.01-0.99)
- Stored as strings in `outcomePrices`: `"[\"0.45\", \"0.55\"]"`
- Stored as numbers in `bestBid`, `bestAsk`, etc.

### Timestamps

All timestamps are ISO 8601 format:
```
2024-12-31T23:59:59.000Z
```

## Key Identifiers

| ID Type | Description | Example |
|---------|-------------|---------|
| `id` | Internal market/event ID | `"12345"` |
| `slug` | URL-friendly identifier | `"bitcoin-100k"` |
| `conditionId` | Gnosis CTF condition | `"0x1234..."` |
| `clobTokenIds` | CLOB trading tokens | `"[\"71321\",\"71322\"]"` |

## Common Query Patterns

### Get active markets with high volume

```bash
curl "https://gamma-api.polymarket.com/markets?active=true&closed=false&volume_num_min=100000&order=volumeNum&ascending=false"
```

### Get markets for a specific event

```bash
# First, get event by slug
curl "https://gamma-api.polymarket.com/events?slug=us-presidential-election-2024"
```

### Get featured events

```bash
curl "https://gamma-api.polymarket.com/events?featured=true"
```

### Get events by tag

```bash
curl "https://gamma-api.polymarket.com/events?tag_slug=crypto"
```

## Understanding Negative Risk Events

Polymarket uses "negative risk" for mutually exclusive outcomes:

- `negRisk: true` - Event has mutually exclusive markets
- `negRiskMarketID` - Contract ID for neg-risk trading
- Sum of YES prices across all markets = 100%

Example: In a "Who will win?" event with 3 candidates:
- Candidate A: 45% ($0.45)
- Candidate B: 35% ($0.35)
- Candidate C: 20% ($0.20)
- Total: 100%

## Trading Integration

For actual trading, you'll need:

1. **CLOB API** for order book trading
2. **Condition IDs** for smart contract interactions
3. **Token IDs** from `clobTokenIds` field

The Gamma API is for market data only.

## Comparison with Kalshi

| Feature | Polymarket | Kalshi |
|---------|------------|--------|
| Pagination | Offset-based | Cursor-based |
| Price format | Decimal (0.45) | Cents (45) |
| ID type | Integer | String ticker |
| Response format | Array | Object with data key |
| Auth | None for read | None for read |
