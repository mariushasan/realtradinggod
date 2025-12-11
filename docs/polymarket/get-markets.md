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
    "id": "<string>",
    "question": "<string>",
    "conditionId": "<string>",
    "slug": "<string>",
    "twitterCardImage": "<string>",
    "resolutionSource": "<string>",
    "endDate": "2023-11-07T05:31:56Z",
    "category": "<string>",
    "ammType": "<string>",
    "liquidity": "<string>",
    "sponsorName": "<string>",
    "sponsorImage": "<string>",
    "startDate": "2023-11-07T05:31:56Z",
    "xAxisValue": "<string>",
    "yAxisValue": "<string>",
    "denominationToken": "<string>",
    "fee": "<string>",
    "image": "<string>",
    "icon": "<string>",
    "lowerBound": "<string>",
    "upperBound": "<string>",
    "description": "<string>",
    "outcomes": "<string>",
    "outcomePrices": "<string>",
    "volume": "<string>",
    "active": true,
    "marketType": "<string>",
    "formatType": "<string>",
    "lowerBoundDate": "<string>",
    "upperBoundDate": "<string>",
    "closed": true,
    "marketMakerAddress": "<string>",
    "createdBy": 123,
    "updatedBy": 123,
    "createdAt": "2023-11-07T05:31:56Z",
    "updatedAt": "2023-11-07T05:31:56Z",
    "closedTime": "<string>",
    "wideFormat": true,
    "new": true,
    "mailchimpTag": "<string>",
    "featured": true,
    "archived": true,
    "resolvedBy": "<string>",
    "restricted": true,
    "marketGroup": 123,
    "groupItemTitle": "<string>",
    "groupItemThreshold": "<string>",
    "questionID": "<string>",
    "umaEndDate": "<string>",
    "enableOrderBook": true,
    "orderPriceMinTickSize": 123,
    "orderMinSize": 123,
    "umaResolutionStatus": "<string>",
    "curationOrder": 123,
    "volumeNum": 123,
    "liquidityNum": 123,
    "endDateIso": "<string>",
    "startDateIso": "<string>",
    "umaEndDateIso": "<string>",
    "hasReviewedDates": true,
    "readyForCron": true,
    "commentsEnabled": true,
    "volume24hr": 123,
    "volume1wk": 123,
    "volume1mo": 123,
    "volume1yr": 123,
    "gameStartTime": "<string>",
    "secondsDelay": 123,
    "clobTokenIds": "<string>",
    "disqusThread": "<string>",
    "shortOutcomes": "<string>",
    "teamAID": "<string>",
    "teamBID": "<string>",
    "umaBond": "<string>",
    "umaReward": "<string>",
    "fpmmLive": true,
    "volume24hrAmm": 123,
    "volume1wkAmm": 123,
    "volume1moAmm": 123,
    "volume1yrAmm": 123,
    "volume24hrClob": 123,
    "volume1wkClob": 123,
    "volume1moClob": 123,
    "volume1yrClob": 123,
    "volumeAmm": 123,
    "volumeClob": 123,
    "liquidityAmm": 123,
    "liquidityClob": 123,
    "makerBaseFee": 123,
    "takerBaseFee": 123,
    "customLiveness": 123,
    "acceptingOrders": true,
    "notificationsEnabled": true,
    "score": 123,
    "imageOptimized": {
      "id": "<string>",
      "imageUrlSource": "<string>",
      "imageUrlOptimized": "<string>",
      "imageSizeKbSource": 123,
      "imageSizeKbOptimized": 123,
      "imageOptimizedComplete": true,
      "imageOptimizedLastUpdated": "<string>",
      "relID": 123,
      "field": "<string>",
      "relname": "<string>"
    },
    "iconOptimized": {
      "id": "<string>",
      "imageUrlSource": "<string>",
      "imageUrlOptimized": "<string>",
      "imageSizeKbSource": 123,
      "imageSizeKbOptimized": 123,
      "imageOptimizedComplete": true,
      "imageOptimizedLastUpdated": "<string>",
      "relID": 123,
      "field": "<string>",
      "relname": "<string>"
    },
    "events": [
      {
        "id": "<string>",
        "ticker": "<string>",
        "slug": "<string>",
        "title": "<string>",
        "subtitle": "<string>",
        "description": "<string>",
        "resolutionSource": "<string>",
        "startDate": "2023-11-07T05:31:56Z",
        "creationDate": "2023-11-07T05:31:56Z",
        "endDate": "2023-11-07T05:31:56Z",
        "image": "<string>",
        "icon": "<string>",
        "active": true,
        "closed": true,
        "archived": true,
        "new": true,
        "featured": true,
        "restricted": true,
        "liquidity": 123,
        "volume": 123,
        "openInterest": 123,
        "sortBy": "<string>",
        "category": "<string>",
        "subcategory": "<string>",
        "isTemplate": true,
        "templateVariables": "<string>",
        "published_at": "<string>",
        "createdBy": "<string>",
        "updatedBy": "<string>",
        "createdAt": "2023-11-07T05:31:56Z",
        "updatedAt": "2023-11-07T05:31:56Z",
        "commentsEnabled": true,
        "competitive": 123,
        "volume24hr": 123,
        "volume1wk": 123,
        "volume1mo": 123,
        "volume1yr": 123,
        "featuredImage": "<string>",
        "disqusThread": "<string>",
        "parentEvent": "<string>",
        "enableOrderBook": true,
        "liquidityAmm": 123,
        "liquidityClob": 123,
        "negRisk": true,
        "negRiskMarketID": "<string>",
        "negRiskFeeBips": 123,
        "commentCount": 123,
        "imageOptimized": {
          "id": "<string>",
          "imageUrlSource": "<string>",
          "imageUrlOptimized": "<string>",
          "imageSizeKbSource": 123,
          "imageSizeKbOptimized": 123,
          "imageOptimizedComplete": true,
          "imageOptimizedLastUpdated": "<string>",
          "relID": 123,
          "field": "<string>",
          "relname": "<string>"
        },
        "iconOptimized": {
          "id": "<string>",
          "imageUrlSource": "<string>",
          "imageUrlOptimized": "<string>",
          "imageSizeKbSource": 123,
          "imageSizeKbOptimized": 123,
          "imageOptimizedComplete": true,
          "imageOptimizedLastUpdated": "<string>",
          "relID": 123,
          "field": "<string>",
          "relname": "<string>"
        },
        "featuredImageOptimized": {
          "id": "<string>",
          "imageUrlSource": "<string>",
          "imageUrlOptimized": "<string>",
          "imageSizeKbSource": 123,
          "imageSizeKbOptimized": 123,
          "imageOptimizedComplete": true,
          "imageOptimizedLastUpdated": "<string>",
          "relID": 123,
          "field": "<string>",
          "relname": "<string>"
        },
        "subEvents": [
          "<string>"
        ],
        "markets": "<array>",
        "series": [
          {
            "id": "<string>",
            "ticker": "<string>",
            "slug": "<string>",
            "title": "<string>",
            "subtitle": "<string>",
            "seriesType": "<string>",
            "recurrence": "<string>",
            "description": "<string>",
            "image": "<string>",
            "icon": "<string>",
            "layout": "<string>",
            "active": true,
            "closed": true,
            "archived": true,
            "new": true,
            "featured": true,
            "restricted": true,
            "isTemplate": true,
            "templateVariables": true,
            "publishedAt": "<string>",
            "createdBy": "<string>",
            "updatedBy": "<string>",
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z",
            "commentsEnabled": true,
            "competitive": "<string>",
            "volume24hr": 123,
            "volume": 123,
            "liquidity": 123,
            "startDate": "2023-11-07T05:31:56Z",
            "pythTokenID": "<string>",
            "cgAssetName": "<string>",
            "score": 123,
            "events": "<array>",
            "collections": [
              {
                "id": "<string>",
                "ticker": "<string>",
                "slug": "<string>",
                "title": "<string>",
                "subtitle": "<string>",
                "collectionType": "<string>",
                "description": "<string>",
                "tags": "<string>",
                "image": "<string>",
                "icon": "<string>",
                "headerImage": "<string>",
                "layout": "<string>",
                "active": true,
                "closed": true,
                "archived": true,
                "new": true,
                "featured": true,
                "restricted": true,
                "isTemplate": true,
                "templateVariables": "<string>",
                "publishedAt": "<string>",
                "createdBy": "<string>",
                "updatedBy": "<string>",
                "createdAt": "2023-11-07T05:31:56Z",
                "updatedAt": "2023-11-07T05:31:56Z",
                "commentsEnabled": true,
                "imageOptimized": {
                  "id": "<string>",
                  "imageUrlSource": "<string>",
                  "imageUrlOptimized": "<string>",
                  "imageSizeKbSource": 123,
                  "imageSizeKbOptimized": 123,
                  "imageOptimizedComplete": true,
                  "imageOptimizedLastUpdated": "<string>",
                  "relID": 123,
                  "field": "<string>",
                  "relname": "<string>"
                },
                "iconOptimized": {
                  "id": "<string>",
                  "imageUrlSource": "<string>",
                  "imageUrlOptimized": "<string>",
                  "imageSizeKbSource": 123,
                  "imageSizeKbOptimized": 123,
                  "imageOptimizedComplete": true,
                  "imageOptimizedLastUpdated": "<string>",
                  "relID": 123,
                  "field": "<string>",
                  "relname": "<string>"
                },
                "headerImageOptimized": {
                  "id": "<string>",
                  "imageUrlSource": "<string>",
                  "imageUrlOptimized": "<string>",
                  "imageSizeKbSource": 123,
                  "imageSizeKbOptimized": 123,
                  "imageOptimizedComplete": true,
                  "imageOptimizedLastUpdated": "<string>",
                  "relID": 123,
                  "field": "<string>",
                  "relname": "<string>"
                }
              }
            ],
            "categories": [
              {
                "id": "<string>",
                "label": "<string>",
                "parentCategory": "<string>",
                "slug": "<string>",
                "publishedAt": "<string>",
                "createdBy": "<string>",
                "updatedBy": "<string>",
                "createdAt": "2023-11-07T05:31:56Z",
                "updatedAt": "2023-11-07T05:31:56Z"
              }
            ],
            "tags": [
              {
                "id": "<string>",
                "label": "<string>",
                "slug": "<string>",
                "forceShow": true,
                "publishedAt": "<string>",
                "createdBy": 123,
                "updatedBy": 123,
                "createdAt": "2023-11-07T05:31:56Z",
                "updatedAt": "2023-11-07T05:31:56Z",
                "forceHide": true,
                "isCarousel": true
              }
            ],
            "commentCount": 123,
            "chats": [
              {
                "id": "<string>",
                "channelId": "<string>",
                "channelName": "<string>",
                "channelImage": "<string>",
                "live": true,
                "startTime": "2023-11-07T05:31:56Z",
                "endTime": "2023-11-07T05:31:56Z"
              }
            ]
          }
        ],
        "categories": [
          {
            "id": "<string>",
            "label": "<string>",
            "parentCategory": "<string>",
            "slug": "<string>",
            "publishedAt": "<string>",
            "createdBy": "<string>",
            "updatedBy": "<string>",
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z"
          }
        ],
        "collections": [
          {
            "id": "<string>",
            "ticker": "<string>",
            "slug": "<string>",
            "title": "<string>",
            "subtitle": "<string>",
            "collectionType": "<string>",
            "description": "<string>",
            "tags": "<string>",
            "image": "<string>",
            "icon": "<string>",
            "headerImage": "<string>",
            "layout": "<string>",
            "active": true,
            "closed": true,
            "archived": true,
            "new": true,
            "featured": true,
            "restricted": true,
            "isTemplate": true,
            "templateVariables": "<string>",
            "publishedAt": "<string>",
            "createdBy": "<string>",
            "updatedBy": "<string>",
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z",
            "commentsEnabled": true,
            "imageOptimized": {
              "id": "<string>",
              "imageUrlSource": "<string>",
              "imageUrlOptimized": "<string>",
              "imageSizeKbSource": 123,
              "imageSizeKbOptimized": 123,
              "imageOptimizedComplete": true,
              "imageOptimizedLastUpdated": "<string>",
              "relID": 123,
              "field": "<string>",
              "relname": "<string>"
            },
            "iconOptimized": {
              "id": "<string>",
              "imageUrlSource": "<string>",
              "imageUrlOptimized": "<string>",
              "imageSizeKbSource": 123,
              "imageSizeKbOptimized": 123,
              "imageOptimizedComplete": true,
              "imageOptimizedLastUpdated": "<string>",
              "relID": 123,
              "field": "<string>",
              "relname": "<string>"
            },
            "headerImageOptimized": {
              "id": "<string>",
              "imageUrlSource": "<string>",
              "imageUrlOptimized": "<string>",
              "imageSizeKbSource": 123,
              "imageSizeKbOptimized": 123,
              "imageOptimizedComplete": true,
              "imageOptimizedLastUpdated": "<string>",
              "relID": 123,
              "field": "<string>",
              "relname": "<string>"
            }
          }
        ],
        "tags": [
          {
            "id": "<string>",
            "label": "<string>",
            "slug": "<string>",
            "forceShow": true,
            "publishedAt": "<string>",
            "createdBy": 123,
            "updatedBy": 123,
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z",
            "forceHide": true,
            "isCarousel": true
          }
        ],
        "cyom": true,
        "closedTime": "2023-11-07T05:31:56Z",
        "showAllOutcomes": true,
        "showMarketImages": true,
        "automaticallyResolved": true,
        "enableNegRisk": true,
        "automaticallyActive": true,
        "eventDate": "<string>",
        "startTime": "2023-11-07T05:31:56Z",
        "eventWeek": 123,
        "seriesSlug": "<string>",
        "score": "<string>",
        "elapsed": "<string>",
        "period": "<string>",
        "live": true,
        "ended": true,
        "finishedTimestamp": "2023-11-07T05:31:56Z",
        "gmpChartMode": "<string>",
        "eventCreators": [
          {
            "id": "<string>",
            "creatorName": "<string>",
            "creatorHandle": "<string>",
            "creatorUrl": "<string>",
            "creatorImage": "<string>",
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z"
          }
        ],
        "tweetCount": 123,
        "chats": [
          {
            "id": "<string>",
            "channelId": "<string>",
            "channelName": "<string>",
            "channelImage": "<string>",
            "live": true,
            "startTime": "2023-11-07T05:31:56Z",
            "endTime": "2023-11-07T05:31:56Z"
          }
        ],
        "featuredOrder": 123,
        "estimateValue": true,
        "cantEstimate": true,
        "estimatedValue": "<string>",
        "templates": [
          {
            "id": "<string>",
            "eventTitle": "<string>",
            "eventSlug": "<string>",
            "eventImage": "<string>",
            "marketTitle": "<string>",
            "description": "<string>",
            "resolutionSource": "<string>",
            "negRisk": true,
            "sortBy": "<string>",
            "showMarketImages": true,
            "seriesSlug": "<string>",
            "outcomes": "<string>"
          }
        ],
        "spreadsMainLine": 123,
        "totalsMainLine": 123,
        "carouselMap": "<string>",
        "pendingDeployment": true,
        "deploying": true,
        "deployingTimestamp": "2023-11-07T05:31:56Z",
        "scheduledDeploymentTimestamp": "2023-11-07T05:31:56Z",
        "gameStatus": "<string>"
      }
    ],
    "categories": [
      {
        "id": "<string>",
        "label": "<string>",
        "parentCategory": "<string>",
        "slug": "<string>",
        "publishedAt": "<string>",
        "createdBy": "<string>",
        "updatedBy": "<string>",
        "createdAt": "2023-11-07T05:31:56Z",
        "updatedAt": "2023-11-07T05:31:56Z"
      }
    ],
    "tags": [
      {
        "id": "<string>",
        "label": "<string>",
        "slug": "<string>",
        "forceShow": true,
        "publishedAt": "<string>",
        "createdBy": 123,
        "updatedBy": 123,
        "createdAt": "2023-11-07T05:31:56Z",
        "updatedAt": "2023-11-07T05:31:56Z",
        "forceHide": true,
        "isCarousel": true
      }
    ],
    "creator": "<string>",
    "ready": true,
    "funded": true,
    "pastSlugs": "<string>",
    "readyTimestamp": "2023-11-07T05:31:56Z",
    "fundedTimestamp": "2023-11-07T05:31:56Z",
    "acceptingOrdersTimestamp": "2023-11-07T05:31:56Z",
    "competitive": 123,
    "rewardsMinSize": 123,
    "rewardsMaxSpread": 123,
    "spread": 123,
    "automaticallyResolved": true,
    "oneDayPriceChange": 123,
    "oneHourPriceChange": 123,
    "oneWeekPriceChange": 123,
    "oneMonthPriceChange": 123,
    "oneYearPriceChange": 123,
    "lastTradePrice": 123,
    "bestBid": 123,
    "bestAsk": 123,
    "automaticallyActive": true,
    "clearBookOnStart": true,
    "chartColor": "<string>",
    "seriesColor": "<string>",
    "showGmpSeries": true,
    "showGmpOutcome": true,
    "manualActivation": true,
    "negRiskOther": true,
    "gameId": "<string>",
    "groupItemRange": "<string>",
    "sportsMarketType": "<string>",
    "line": 123,
    "umaResolutionStatuses": "<string>",
    "pendingDeployment": true,
    "deploying": true,
    "deployingTimestamp": "2023-11-07T05:31:56Z",
    "scheduledDeploymentTimestamp": "2023-11-07T05:31:56Z",
    "rfqEnabled": true,
    "eventStartTime": "2023-11-07T05:31:56Z"
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
