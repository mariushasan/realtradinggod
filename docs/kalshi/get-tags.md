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
{'tags_by_categories': {'Climate and Weather': ['Hurricanes', 'Climate change', 'Daily temperature', 'Natural disasters', 'Snow and rain'], 'Companies': ['CEOs', 'Elon Musk', 'Earnings Mention', 'Product launches', 'KPIs', 'Layoffs'], 'Crypto': ['Pre-Market', 'SOL', 'BTC', 'Hourly', 'ETH', 'SHIBA', 'Dogecoin'], 'Economics': ['Inflation', 'Fed', 'Growth', 'Employment', 'Oil and energy'], 'Education': None, 'Elections': None, 'Entertainment': ['Music', 'Music charts', 'Awards', 'Movies', 'Golden Globes', 'Oscars', 'Video games', 'Television', 'StockX', 'Live Music', 'Rotten Tomatoes', 'Music Streams', 'Morgan Wallen'], 'Financials': ['S&P', 'Daily', 'EUR/USD', 'Nasdaq', 'Treasuries', 'USD/JPY', 'WTI'], 'Health': ['Diseases', 'Health Tech', 'FDA Approval', 'Drug Prices', 'Vaccines'], 'Mentions': None, 'Politics': ['Trump Agenda', 'Culture war', 'Bills', 'Foreign Elections', 'SCOTUS & courts', 'US Elections', 'Education', 'Debt ceiling & shutdowns', 'Immigration', 'Approval ratings', 'Cabinet', 'Trump Policies', 'Confirmations', 'Elections', 'Policy'], 'Science and Technology': ['AI', 'AI Transfers', 'Space', 'Energy', 'Papers', 'Medicine'], 'Social': None, 'Sports': ['Football', 'Soccer', 'Basketball', 'Hockey', 'Esports', 'UFC', 'Chess', 'Baseball', 'NFL', 'Cricket', 'Boxing', 'Golf', 'MMA', 'Motorsport'], 'Transportation': ['Airlines & aviation'], 'World': ['Foreign economies']}}
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
