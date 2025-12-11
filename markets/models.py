from django.db import models


class Exchange(models.TextChoices):
    KALSHI = 'kalshi', 'Kalshi'
    POLYMARKET = 'polymarket', 'Polymarket'


class Tag(models.Model):
    """Tag for categorizing markets on exchanges"""
    exchange = models.CharField(max_length=20, choices=Exchange.choices)

    # External identifier from the API (not our primary key)
    external_id = models.CharField(max_length=255, blank=True, help_text="API's internal ID")

    # Tag info
    label = models.CharField(max_length=255)  # Display name
    slug = models.CharField(max_length=255, blank=True)  # URL-friendly identifier (Polymarket)
    category = models.CharField(max_length=255, blank=True)  # Category name (Kalshi)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['exchange', 'label', 'category']
        ordering = ['exchange', 'category', 'label']

    def __str__(self):
        if self.category:
            return f"[{self.exchange}] {self.category}: {self.label}"
        return f"[{self.exchange}] {self.label}"


class TagMatch(models.Model):
    """Match between tags from different exchanges (cross-exchange tag matching)"""
    kalshi_tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='kalshi_tag_matches',
        limit_choices_to={'exchange': Exchange.KALSHI}
    )
    polymarket_tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='polymarket_tag_matches',
        limit_choices_to={'exchange': Exchange.POLYMARKET}
    )

    # NLP matching info
    similarity_score = models.FloatField(default=0.0)
    match_reason = models.TextField(blank=True, help_text="Why these tags were matched")

    # Manual vs auto match
    is_manual = models.BooleanField(default=False, help_text="True if manually created by user")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['kalshi_tag', 'polymarket_tag']
        ordering = ['-similarity_score', '-updated_at']

    def __str__(self):
        return f"TagMatch: {self.kalshi_tag.label} <-> {self.polymarket_tag.label}"


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

    # Tags associated with this event (for filtering and sports detection)
    tags = models.ManyToManyField('Tag', related_name='events', blank=True)

    # Raw API data for sports matching (stored as JSON)
    raw_data = models.JSONField(default=dict, blank=True)

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

    def has_sports_tag(self) -> bool:
        """Check if this event has any sports-related tags"""
        return self.tags.filter(
            models.Q(category__icontains='sports') |
            models.Q(label__icontains='sports') |
            models.Q(label__icontains='nfl') |
            models.Q(label__icontains='nba') |
            models.Q(label__icontains='mlb') |
            models.Q(label__icontains='nhl')
        ).exists()


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

    # Tags associated with this market (for filtering)
    tags = models.ManyToManyField(Tag, related_name='markets', blank=True)

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


class SportsEvent(models.Model):
    """Sports event with extracted fields for matching"""

    class League(models.TextChoices):
        NFL = 'nfl', 'NFL'
        NBA = 'nba', 'NBA'
        MLB = 'mlb', 'MLB'
        NHL = 'nhl', 'NHL'
        MLS = 'mls', 'MLS'
        UFC = 'ufc', 'UFC'
        NCAA_FB = 'ncaa_fb', 'NCAA Football'
        NCAA_BB = 'ncaa_bb', 'NCAA Basketball'
        OTHER = 'other', 'Other'

    class MarketType(models.TextChoices):
        WIN_TOTAL = 'win_total', 'Win Total (Over/Under)'
        EXACT_WINS = 'exact_wins', 'Exact Win Total'
        DIVISION_WINNER = 'division', 'Division Winner'
        CONFERENCE_WINNER = 'conference', 'Conference Winner'
        CHAMPION = 'champion', 'League Champion / Super Bowl'
        PLAYOFF_WINNER = 'playoff', 'Playoff Game Winner'
        MVP = 'mvp', 'MVP Award'
        PLAYER_AWARD = 'player_award', 'Player Award'
        PROP_BET = 'prop', 'Prop Bet'
        OTHER = 'other', 'Other'

    # Link to the base Event
    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name='sports_event',
        primary_key=True
    )

    # Core identification
    league = models.CharField(max_length=20, choices=League.choices, default=League.OTHER)
    market_type = models.CharField(max_length=20, choices=MarketType.choices, default=MarketType.OTHER)

    # Team info (extracted from ticker/title/images)
    team_code = models.CharField(max_length=10, blank=True, help_text="Standard team abbreviation (e.g., CLE, LAR, TB)")
    team_name = models.CharField(max_length=100, blank=True, help_text="Full team name or city (e.g., Cleveland, Tampa Bay)")
    team_uuid = models.CharField(max_length=100, blank=True, help_text="Kalshi's internal team UUID")

    # Player info (for MVP/awards markets)
    player_name = models.CharField(max_length=200, blank=True, help_text="Player name for awards markets")

    # Season/timing
    season = models.CharField(max_length=20, blank=True, help_text="Season identifier (e.g., 2025-26, 2025)")
    season_year = models.IntegerField(null=True, blank=True, help_text="Primary year of the season")

    # Division/Conference
    division = models.CharField(max_length=50, blank=True, help_text="Division name (e.g., NFC West)")
    conference = models.CharField(max_length=20, blank=True, help_text="Conference (e.g., NFC, AFC, Eastern)")

    # Numeric thresholds (for win totals)
    threshold_value = models.FloatField(null=True, blank=True, help_text="Numeric threshold (e.g., 8.5 for over 8.5 wins)")
    threshold_type = models.CharField(max_length=20, blank=True, help_text="Type of threshold (over, under, exactly)")

    # Kalshi-specific fields
    series_ticker = models.CharField(max_length=100, blank=True, help_text="Kalshi series ticker")
    competition_scope = models.CharField(max_length=100, blank=True, help_text="Kalshi competition_scope")

    # Polymarket-specific fields
    group_item_title = models.CharField(max_length=200, blank=True, help_text="Polymarket groupItemTitle")
    image_team_code = models.CharField(max_length=10, blank=True, help_text="Team code extracted from image URL")

    # Matching helpers
    normalized_title = models.CharField(max_length=500, blank=True, help_text="Normalized title for text matching")
    keywords = models.JSONField(default=list, blank=True, help_text="Extracted keywords for matching")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        parts = [f"[{self.league}]"]
        if self.team_code:
            parts.append(self.team_code)
        if self.market_type:
            parts.append(f"({self.get_market_type_display()})")
        parts.append(self.event.title[:50])
        return ' '.join(parts)


class SportsEventMatch(models.Model):
    """Match between sports events from different exchanges"""
    kalshi_sports_event = models.ForeignKey(
        SportsEvent,
        on_delete=models.CASCADE,
        related_name='kalshi_sports_matches',
        limit_choices_to={'event__exchange': Exchange.KALSHI}
    )
    polymarket_sports_event = models.ForeignKey(
        SportsEvent,
        on_delete=models.CASCADE,
        related_name='polymarket_sports_matches',
        limit_choices_to={'event__exchange': Exchange.POLYMARKET}
    )

    # Matching scores by method
    similarity_score = models.FloatField(default=0.0)
    team_code_match = models.BooleanField(default=False, help_text="Teams matched by code")
    team_name_match = models.BooleanField(default=False, help_text="Teams matched by name")
    league_match = models.BooleanField(default=False, help_text="Same league")
    market_type_match = models.BooleanField(default=False, help_text="Same market type")
    season_match = models.BooleanField(default=False, help_text="Same season")
    threshold_match = models.BooleanField(default=False, help_text="Same threshold value")

    # Match reason breakdown
    match_reason = models.TextField(blank=True, help_text="Detailed explanation of why matched")
    match_method = models.CharField(max_length=50, blank=True, help_text="Primary matching method used")

    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['kalshi_sports_event', 'polymarket_sports_event']
        ordering = ['-similarity_score', '-updated_at']

    def __str__(self):
        return f"SportsMatch: {self.kalshi_sports_event.team_code or 'Kalshi'} <-> {self.polymarket_sports_event.team_code or 'Poly'}"


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
