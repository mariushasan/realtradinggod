Get Market
Endpoint for getting data about a specific market by its ticker. A market represents a specific binary outcome within an event that users can trade on (e.g., “Will candidate X win?”). Markets have yes/no positions, current prices, volume, and settlement rules.

GET
/
markets
/
{ticker}

Try it
Path Parameters
​
ticker
stringrequired
Market ticker

Response

200

application/json
Market retrieved successfully

url https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}