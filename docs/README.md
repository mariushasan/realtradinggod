# Prediction Markets API Documentation

This documentation covers the APIs for two prediction market platforms: **Kalshi** and **Polymarket**. Use these docs as a reference for building arbitrage analyzers, market data tools, and trading bots.

## Quick Reference

| Platform | Base URL | Auth Required |
|----------|----------|---------------|
| Kalshi | `https://api.elections.kalshi.com/trade-api/v2` | Yes (for trading) |
| Polymarket | `https://gamma-api.polymarket.com` | No (read-only) |

## Endpoints Overview

### Kalshi Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/markets` | GET | List all markets with filtering options |
| `/markets/{ticker}` | GET | Get a specific market by ticker |
| `/events` | GET | List all events |
| `/events/{event_ticker}` | GET | Get a specific event by ticker |
| `/search/tags_by_categories` | GET | Get tags grouped by categories |

### Polymarket Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/markets` | GET | List all markets with filtering options |
| `/markets/{id}` | GET | Get a specific market by ID |
| `/events` | GET | List all events |
| `/events/{id}` | GET | Get a specific event by ID |
| `/tags` | GET | List all tags |

## Key Concepts

### Markets vs Events

- **Event**: A real-world occurrence (election, sports game, economic indicator)
- **Market**: A specific tradeable outcome within an event (e.g., "Will candidate X win?")

### Platform Differences

| Feature | Kalshi | Polymarket |
|---------|--------|------------|
| Market Identifier | `ticker` (string) | `id` (integer) |
| Event Identifier | `event_ticker` (string) | `id` (integer) |
| Pagination | Cursor-based | Offset-based |
| Price Format | Cents (1-99) | Decimal (0.01-0.99) |

## File Structure

```
docs/
├── README.md                    # This file
├── kalshi/
│   ├── api-reference.md         # Full API reference
│   ├── get-markets.md           # GET /markets
│   ├── get-market-by-id.md      # GET /markets/{ticker}
│   ├── get-events.md            # GET /events
│   ├── get-event-by-id.md       # GET /events/{event_ticker}
│   ├── get-tags.md              # GET /search/tags_by_categories
│   └── kalshiopenapi.yaml       # OpenAPI specification
└── polymarket/
    ├── api-reference.md         # Full API reference
    ├── get-markets.md           # GET /markets
    ├── get-market-by-id.md      # GET /markets/{id}
    ├── get-events.md            # GET /events
    ├── get-event-by-id.md       # GET /events/{id}
    └── get-tags.md              # GET /tags
```
