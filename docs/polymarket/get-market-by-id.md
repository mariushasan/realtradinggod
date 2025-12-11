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
