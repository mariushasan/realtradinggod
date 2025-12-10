Get Markets
Filter by market status. Possible values: unopened, open, closed, settled. Leave empty to return markets with any status.

Only one status filter may be supplied at a time.
Timestamp filters will be mutually exclusive from other timestamp filters and certain status filters.
Compatible Timestamp Filters	Additional Status Filters
min_created_ts, max_created_ts	unopened, open, empty
min_close_ts, max_close_ts	closed, empty
min_settled_ts, max_settled_ts	settled, empty
GET
/
markets

Try it
Query Parameters
​
limit
integer<int64>default:100
Number of results per page. Defaults to 100. Maximum value is 1000.

Required range: 1 <= x <= 1000
​
cursor
string
Pagination cursor. Use the cursor value returned from the previous response to get the next page of results. Leave empty for the first page.

​
event_ticker
string
Event ticker of desired positions. Multiple event tickers can be provided as a comma-separated list (maximum 10).

​
series_ticker
string
Filter by series ticker

​
min_created_ts
integer<int64>
Filter items that created after this Unix timestamp

​
max_created_ts
integer<int64>
Filter items that created before this Unix timestamp

​
max_close_ts
integer<int64>
Filter items that close before this Unix timestamp

​
min_close_ts
integer<int64>
Filter items that close after this Unix timestamp

​
min_settled_ts
integer<int64>
Filter items that settled after this Unix timestamp

​
max_settled_ts
integer<int64>
Filter items that settled before this Unix timestamp

​
status
string
Filter by market status. Possible values are 'unopened', 'open', 'closed', 'settled'. Leave empty to return markets with any status.

​
tickers
string
Filter by specific market tickers. Comma-separated list of market tickers to retrieve.

​
mve_filter
enum<string>
Filter by multivariate events (combos). 'only' returns only multivariate events, 'exclude' excludes multivariate events.

Available options: only, exclude 
Response

200

application/json
Markets retrieved successfully

url https://api.elections.kalshi.com/trade-api/v2/markets?limit=100