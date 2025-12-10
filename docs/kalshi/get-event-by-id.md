Get Event
Endpoint for getting data about an event by its ticker. An event represents a real-world occurrence that can be traded on, such as an election, sports game, or economic indicator release. Events contain one or more markets where users can place trades on different outcomes.

GET
/
events
/
{event_ticker}

Try it
Path Parameters
​
event_ticker
stringrequired
Event ticker

Query Parameters
​
with_nested_markets
booleandefault:false
If true, markets are included within the event object. If false (default), markets are returned as a separate top-level field in the response.

Response

200

application/json
Event retrieved successfully

​
event
objectrequired
Data for the event.

Show child attributes

​
markets
object[]required
Data for the markets in this event. This field is deprecated in favour of the "markets" field inside the event. Which will be filled with the same value if you use the query parameter "with_nested_markets=true".

url https://api.elections.kalshi.com/trade-api/v2/events/{event_ticker}