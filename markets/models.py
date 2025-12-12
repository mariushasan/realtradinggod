from django.db import models


class Exchange(models.TextChoices):
    KALSHI = 'kalshi', 'Kalshi'
    POLYMARKET = 'polymarket', 'Polymarket'


class Event(models.Model):
    """Event from either Kalshi or Polymarket - container for related markets"""
    exchange = models.CharField(max_length=20, choices=Exchange.choices)

    # External identifiers
    external_id = models.CharField(max_length=255)  # event_ticker for Kalshi, id/slug for Polymarket

    # Event info
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=255, blank=True)

    # URL for linking to the event
    url = models.URLField(max_length=500, blank=True)

    # Raw API response data
    raw_data = models.JSONField(default=dict, help_text="Raw API response for this event")

    # Trading metrics (aggregated from markets)
    volume = models.FloatField(default=0.0)
    volume_24h = models.FloatField(default=0.0)
    liquidity = models.FloatField(default=0.0)
    open_interest = models.FloatField(default=0.0)

    # Status
    is_active = models.BooleanField(default=True)
    mutually_exclusive = models.BooleanField(default=False)

    # Timestamps
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['exchange', 'external_id']
        ordering = ['-updated_at']

    def __str__(self):
        return f"[{self.exchange}] {self.title}"


class Market(models.Model):
    """Single market from either Kalshi or Polymarket"""
    exchange = models.CharField(max_length=20, choices=Exchange.choices)

    # External identifiers
    external_id = models.CharField(max_length=255)  # token_id for Polymarket, ticker for Kalshi

    # Link to parent event
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='markets',
        null=True,
        blank=True
    )
    event_external_id = models.CharField(max_length=255, blank=True)  # event_ticker for Kalshi, condition_id for Polymarket

    # Market info
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)

    # Outcomes - stored as JSON for flexibility
    # Format: [{"name": "Yes", "price": 0.65}, {"name": "No", "price": 0.35}]
    outcomes = models.JSONField(default=list)

    # URLs for linking
    url = models.URLField(max_length=500, blank=True)

    # Trading metrics
    volume = models.FloatField(default=0.0)
    volume_24h = models.FloatField(default=0.0)
    liquidity = models.FloatField(default=0.0)
    open_interest = models.FloatField(default=0.0)

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


class EventMatch(models.Model):
    """Match between events from different exchanges (cross-exchange event matching)"""
    kalshi_event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='kalshi_matches',
        limit_choices_to={'exchange': Exchange.KALSHI}
    )
    polymarket_event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='polymarket_matches',
        limit_choices_to={'exchange': Exchange.POLYMARKET}
    )

    # NLP matching info
    similarity_score = models.FloatField(default=0.0)
    match_reason = models.TextField(blank=True, help_text="Why these events were matched")

    # Manual verification
    is_verified = models.BooleanField(default=False, help_text="Manually verified as same event")
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['kalshi_event', 'polymarket_event']
        ordering = ['-similarity_score', '-updated_at']

    def __str__(self):
        return f"EventMatch: {self.kalshi_event.title[:30]} <-> {self.polymarket_event.title[:30]}"


class ArbitrageOpportunity(models.Model):
    """Detected arbitrage opportunity"""

    class ArbitrageType(models.TextChoices):
        KALSHI_ONLY = 'kalshi_only', 'Kalshi Only'
        POLYMARKET_ONLY = 'polymarket_only', 'Polymarket Only'
        CROSS_EXCHANGE = 'cross_exchange', 'Cross Exchange'

    arb_type = models.CharField(max_length=20, choices=ArbitrageType.choices)

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
