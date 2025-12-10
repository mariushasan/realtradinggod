Path Parameters
​
id
integerrequired
Query Parameters
​
include_tag
boolean
Response

200

application/json
Market

​
id
string
​
question
string | null
​
conditionId
string
​
slug
string | null
​
twitterCardImage
string | null
​
resolutionSource
string | null
​
endDate
string<date-time> | null
​
category
string | null
​
ammType
string | null
​
liquidity
string | null
​
sponsorName
string | null
​
sponsorImage
string | null
​
startDate
string<date-time> | null
​
xAxisValue
string | null
​
yAxisValue
string | null
​
denominationToken
string | null
​
fee
string | null
​
image
string | null
​
icon
string | null
​
lowerBound
string | null
​
upperBound
string | null
​
description
string | null
​
outcomes
string | null
​
outcomePrices
string | null
​
volume
string | null
​
active
boolean | null
​
marketType
string | null
​
formatType
string | null
​
lowerBoundDate
string | null
​
upperBoundDate
string | null
​
closed
boolean | null
​
marketMakerAddress
string
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
closedTime
string | null
​
wideFormat
boolean | null
​
new
boolean | null
​
mailchimpTag
string | null
​
featured
boolean | null
​
archived
boolean | null
​
resolvedBy
string | null
​
restricted
boolean | null
​
marketGroup
integer | null
​
groupItemTitle
string | null
​
groupItemThreshold
string | null
​
questionID
string | null
​
umaEndDate
string | null
​
enableOrderBook
boolean | null
​
orderPriceMinTickSize
number | null
​
orderMinSize
number | null
​
umaResolutionStatus
string | null
​
curationOrder
integer | null
​
volumeNum
number | null
​
liquidityNum
number | null
​
endDateIso
string | null
​
startDateIso
string | null
​
umaEndDateIso
string | null
​
hasReviewedDates
boolean | null
​
readyForCron
boolean | null
​
commentsEnabled
boolean | null
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
gameStartTime
string | null
​
secondsDelay
integer | null
​
clobTokenIds
string | null
​
disqusThread
string | null
​
shortOutcomes
string | null
​
teamAID
string | null
​
teamBID
string | null
​
umaBond
string | null
​
umaReward
string | null
​
fpmmLive
boolean | null
​
volume24hrAmm
number | null
​
volume1wkAmm
number | null
​
volume1moAmm
number | null
​
volume1yrAmm
number | null
​
volume24hrClob
number | null
​
volume1wkClob
number | null
​
volume1moClob
number | null
​
volume1yrClob
number | null
​
volumeAmm
number | null
​
volumeClob
number | null
​
liquidityAmm
number | null
​
liquidityClob
number | null
​
makerBaseFee
integer | null
​
takerBaseFee
integer | null
​
customLiveness
integer | null
​
acceptingOrders
boolean | null
​
notificationsEnabled
boolean | null
​
score
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
events
object[]
Show child attributes

​
categories
object[]
Show child attributes

​
tags
object[]
Show child attributes

​
creator
string | null
​
ready
boolean | null
​
funded
boolean | null
​
pastSlugs
string | null
​
readyTimestamp
string<date-time> | null
​
fundedTimestamp
string<date-time> | null
​
acceptingOrdersTimestamp
string<date-time> | null
​
competitive
number | null
​
rewardsMinSize
number | null
​
rewardsMaxSpread
number | null
​
spread
number | null
​
automaticallyResolved
boolean | null
​
oneDayPriceChange
number | null
​
oneHourPriceChange
number | null
​
oneWeekPriceChange
number | null
​
oneMonthPriceChange
number | null
​
oneYearPriceChange
number | null
​
lastTradePrice
number | null
​
bestBid
number | null
​
bestAsk
number | null
​
automaticallyActive
boolean | null
​
clearBookOnStart
boolean | null
​
chartColor
string | null
​
seriesColor
string | null
​
showGmpSeries
boolean | null
​
showGmpOutcome
boolean | null
​
manualActivation
boolean | null
​
negRiskOther
boolean | null
​
gameId
string | null
​
groupItemRange
string | null
​
sportsMarketType
string | null
​
line
number | null
​
umaResolutionStatuses
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
​
rfqEnabled
boolean | null
​
eventStartTime
string<date-time> | null

url https://gamma-api.polymarket.com/markets/{id}