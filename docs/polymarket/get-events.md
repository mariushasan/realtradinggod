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
id
integer[]
​
tag_id
integer
​
exclude_tag_id
integer[]
​
slug
string[]
​
tag_slug
string
​
related_tags
boolean
​
active
boolean
​
archived
boolean
​
featured
boolean
​
cyom
boolean
​
include_chat
boolean
​
include_template
boolean
​
recurrence
string
​
closed
boolean
​
liquidity_min
number
​
liquidity_max
number
​
volume_min
number
​
volume_max
number
​
start_date_min
string<date-time>
​
start_date_max
string<date-time>
​
end_date_min
string<date-time>
​
end_date_max
string<date-time>
Response
200 - application/json
List of events

​
id
string
​
ticker
string | null
​
slug
string | null
​
title
string | null
​
subtitle
string | null
​
description
string | null
​
resolutionSource
string | null
​
startDate
string<date-time> | null
​
creationDate
string<date-time> | null
​
endDate
string<date-time> | null
​
image
string | null
​
icon
string | null
​
active
boolean | null
​
closed
boolean | null
​
archived
boolean | null
​
new
boolean | null
​
featured
boolean | null
​
restricted
boolean | null
​
liquidity
number | null
​
volume
number | null
​
openInterest
number | null
​
sortBy
string | null
​
category
string | null
​
subcategory
string | null
​
isTemplate
boolean | null
​
templateVariables
string | null
​
published_at
string | null
​
createdBy
string | null
​
updatedBy
string | null
​
createdAt
string<date-time> | null
​
updatedAt
string<date-time> | null
​
commentsEnabled
boolean | null
​
competitive
number | null
​
volume24hr
number | null
​
volume1wk
number | null
​
volume1mo
number | null
​
volume1yr
number | null
​
featuredImage
string | null
​
disqusThread
string | null
​
parentEvent
string | null
​
enableOrderBook
boolean | null
​
liquidityAmm
number | null
​
liquidityClob
number | null
​
negRisk
boolean | null
​
negRiskMarketID
string | null
​
negRiskFeeBips
integer | null
​
commentCount
integer | null
​
imageOptimized
object
Show child attributes

​
iconOptimized
object
Show child attributes

​
featuredImageOptimized
object
Show child attributes

​
subEvents
string[] | null
​
markets
object[]
Show child attributes

​
series
object[]
Show child attributes

​
categories
object[]
Show child attributes

​
collections
object[]
Show child attributes

​
tags
object[]
Show child attributes

​
cyom
boolean | null
​
closedTime
string<date-time> | null
​
showAllOutcomes
boolean | null
​
showMarketImages
boolean | null
​
automaticallyResolved
boolean | null
​
enableNegRisk
boolean | null
​
automaticallyActive
boolean | null
​
eventDate
string | null
​
startTime
string<date-time> | null
​
eventWeek
integer | null
​
seriesSlug
string | null
​
score
string | null
​
elapsed
string | null
​
period
string | null
​
live
boolean | null
​
ended
boolean | null
​
finishedTimestamp
string<date-time> | null
​
gmpChartMode
string | null
​
eventCreators
object[]
Show child attributes

​
tweetCount
integer | null
​
chats
object[]
Show child attributes

​
featuredOrder
integer | null
​
estimateValue
boolean | null
​
cantEstimate
boolean | null
​
estimatedValue
string | null
​
templates
object[]
Show child attributes

​
spreadsMainLine
number | null
​
totalsMainLine
number | null
​
carouselMap
string | null
​
pendingDeployment
boolean | null
​
deploying
boolean | null
​
deployingTimestamp
string<date-time> | null
​
scheduledDeploymentTimestamp
string<date-time> | null