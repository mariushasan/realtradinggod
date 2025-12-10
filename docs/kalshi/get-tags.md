# Kalshi: Get Tags by Categories

Retrieve all tags organized by their categories. Tags are used to categorize and filter events.

## Endpoint

```
GET https://api.elections.kalshi.com/trade-api/v2/search/tags_by_categories
```

## Authentication

Not required.

## Query Parameters

None.

## Example Request

```bash
curl "https://api.elections.kalshi.com/trade-api/v2/search/tags_by_categories"
```

## Response

```json
{
  "tags_by_categories": {
    "Politics": [
      {
        "tag": "us-elections",
        "label": "US Elections",
        "count": 150
      },
      {
        "tag": "congress",
        "label": "Congress",
        "count": 45
      }
    ],
    "Economics": [
      {
        "tag": "fed",
        "label": "Federal Reserve",
        "count": 30
      },
      {
        "tag": "inflation",
        "label": "Inflation",
        "count": 25
      }
    ],
    "Sports": [
      {
        "tag": "nfl",
        "label": "NFL",
        "count": 100
      }
    ]
  }
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `tags_by_categories` | object | Map of category names to arrays of tags |

### Tag Object

| Field | Type | Description |
|-------|------|-------------|
| `tag` | string | Tag identifier (slug) |
| `label` | string | Human-readable tag name |
| `count` | integer | Number of events with this tag |

## Common Categories

- **Politics** - Elections, legislation, government
- **Economics** - Fed, inflation, GDP, employment
- **Sports** - NFL, NBA, MLB, etc.
- **Entertainment** - Movies, TV, awards
- **Science** - Space, technology, research
- **Weather** - Temperature, storms, climate

## Notes

- Use tags to filter events when searching
- Tags are hierarchical - categories contain multiple tags
- Tag counts indicate the number of active events
