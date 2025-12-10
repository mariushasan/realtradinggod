from django.db import models


class Exchange(models.TextChoices):
    KALSHI = 'kalshi', 'Kalshi'
    POLYMARKET = 'polymarket', 'Polymarket'


class Market(models.Model):
    """Single market from either Kalshi or Polymarket"""
    exchange = models.CharField(max_length=20, choices=Exchange.choices)

    # External identifiers
    external_id = models.CharField(max_length=255)  # token_id for Polymarket, ticker for Kalshi
    event_external_id = models.CharField(max_length=255, blank=True)  # event_ticker for Kalshi, condition_id for Polymarket

    # Market info
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)

    # Outcomes - stored as JSON for flexibility
    # Format: [{"name": "Yes", "price": 0.65}, {"name": "No", "price": 0.35}]
    outcomes = models.JSONField(default=list)

    # URLs for linking
    url = models.URLField(max_length=500, blank=True)

    # Status
    is_active = models.BooleanField(default=True)

    # Timestamps
    close_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['exchange', 'external_id']

    def __str__(self):
        return f"[{self.exchange}] {self.title}"


class MarketMatch(models.Model):
    """Match between markets from different exchanges (cross-exchange matching)"""
    kalshi_market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        related_name='kalshi_matches',
        limit_choices_to={'exchange': Exchange.KALSHI}
    )
    polymarket_market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        related_name='polymarket_matches',
        limit_choices_to={'exchange': Exchange.POLYMARKET}
    )

    # NLP matching info
    similarity_score = models.FloatField(default=0.0)
    match_reason = models.TextField(blank=True, help_text="Why these markets were matched")

    # Manual verification
    is_verified = models.BooleanField(default=False, help_text="Manually verified as same event")
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['kalshi_market', 'polymarket_market']

    def __str__(self):
        return f"Match: {self.kalshi_market.title[:30]} <-> {self.polymarket_market.title[:30]}"


class ArbitrageOpportunity(models.Model):
    """Detected arbitrage opportunity"""

    class ArbitrageType(models.TextChoices):
        KALSHI_ONLY = 'kalshi_only', 'Kalshi Only'
        POLYMARKET_ONLY = 'polymarket_only', 'Polymarket Only'
        CROSS_EXCHANGE = 'cross_exchange', 'Cross Exchange'

    arb_type = models.CharField(max_length=20, choices=ArbitrageType.choices)

    # For same-exchange arb, we might have multiple markets in same event
    # For cross-exchange arb, we use the match
    market_match = models.ForeignKey(
        MarketMatch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='arbitrage_opportunities'
    )

    # For single-exchange arbitrage
    markets = models.ManyToManyField(Market, related_name='arbitrage_opportunities')

    # Arbitrage details - stored as JSON
    # Format: {"positions": [{"market_id": 1, "outcome": "Yes", "price": 0.45}], "total_cost": 0.95, "guaranteed_return": 1.0}
    positions = models.JSONField(default=dict)

    # Calculated values
    profit_percent = models.FloatField()
    expected_value = models.FloatField()

    # Status
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-profit_percent', '-updated_at']

    def __str__(self):
        return f"Arb ({self.arb_type}): {self.profit_percent:.2f}% profit"
