from django.contrib import admin
from .models import Event, Market, EventMatch


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'exchange', 'external_id', 'volume', 'is_active', 'end_date']
    list_filter = ['exchange', 'is_active']
    search_fields = ['title', 'external_id']
    ordering = ['-updated_at']


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['title', 'exchange', 'external_id', 'event', 'volume', 'is_active']
    list_filter = ['exchange', 'is_active']
    search_fields = ['title', 'external_id']
    ordering = ['-updated_at']


@admin.register(EventMatch)
class EventMatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'kalshi_event', 'polymarket_event', 'similarity_score', 'is_verified']
    list_filter = ['is_verified']
    ordering = ['-similarity_score']
