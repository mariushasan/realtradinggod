Query Parameters
​
limit
integer
Required range: x >= 0
​
offset
integer
Required range: x >= 0
​
order
string
Comma-separated list of fields to order by

​
ascending
boolean
​
include_template
boolean
​
is_carousel
boolean
Response
200 - application/json
List of tags

​
id
string
​
label
string | null
​
slug
string | null
​
forceShow
boolean | null
​
publishedAt
string | null
​
createdBy
integer | null
​
updatedBy
integer | null
​
createdAt
string<date-time> | null
​
updatedAt
string<date-time> | null
​
forceHide
boolean | null
​
isCarousel
boolean | null

url https://gamma-api.polymarket.com/tags