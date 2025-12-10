# Polymarket: Get Tags

Retrieve a list of all tags used to categorize events and markets.

## Endpoint

```
GET https://gamma-api.polymarket.com/tags
```

## Authentication

Not required.

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | - | Results per page (≥0) |
| `offset` | integer | No | 0 | Number of results to skip |
| `order` | string | No | - | Comma-separated fields to order by |
| `ascending` | boolean | No | false | Sort direction |
| `include_template` | boolean | No | false | Include template data |
| `is_carousel` | boolean | No | - | Filter carousel tags |

## Example Request

```bash
curl "https://gamma-api.polymarket.com/tags?limit=20"
```

## Response

```json
[
  {
    "id": "1",
    "label": "Crypto",
    "slug": "crypto",
    "forceShow": true,
    "forceHide": false,
    "isCarousel": true,
    "publishedAt": "2023-01-01T00:00:00.000Z",
    "createdAt": "2023-01-01T00:00:00.000Z",
    "updatedAt": "2024-06-15T00:00:00.000Z",
    "createdBy": 1,
    "updatedBy": 1
  },
  {
    "id": "2",
    "label": "Politics",
    "slug": "politics",
    "forceShow": true,
    "forceHide": false,
    "isCarousel": true,
    "publishedAt": "2023-01-01T00:00:00.000Z",
    "createdAt": "2023-01-01T00:00:00.000Z",
    "updatedAt": "2024-06-15T00:00:00.000Z"
  },
  {
    "id": "3",
    "label": "Sports",
    "slug": "sports",
    "forceShow": true,
    "forceHide": false,
    "isCarousel": true
  },
  {
    "id": "4",
    "label": "Pop Culture",
    "slug": "pop-culture",
    "forceShow": false,
    "forceHide": false,
    "isCarousel": false
  }
]
```

## Response Fields

### Tag Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique tag identifier |
| `label` | string | Human-readable tag name |
| `slug` | string | URL-friendly identifier |
| `forceShow` | boolean | Tag is forced to show |
| `forceHide` | boolean | Tag is hidden |
| `isCarousel` | boolean | Tag appears in carousel |
| `publishedAt` | string | Publication timestamp |
| `createdAt` | string | Creation timestamp |
| `updatedAt` | string | Last update timestamp |
| `createdBy` | integer | Creator user ID |
| `updatedBy` | integer | Last updater user ID |

## Common Tags

| Slug | Label | Description |
|------|-------|-------------|
| `crypto` | Crypto | Cryptocurrency markets |
| `politics` | Politics | Political events and elections |
| `sports` | Sports | Sports betting markets |
| `pop-culture` | Pop Culture | Entertainment and celebrities |
| `business` | Business | Business and economics |
| `science` | Science | Science and technology |
| `world` | World | Global events |

## Usage

Tags can be used to filter events and markets:

```bash
# Get events with specific tag
curl "https://gamma-api.polymarket.com/events?tag_slug=crypto"

# Get markets with tag ID
curl "https://gamma-api.polymarket.com/markets?tag_id=1"
```

## Notes

- Use `slug` for URL-friendly filtering
- Use `id` for programmatic filtering
- `forceShow` tags appear prominently in the UI
- `isCarousel` tags appear in the homepage carousel
- Tags provide a flat structure (unlike Kalshi's hierarchical categories)
