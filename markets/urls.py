from django.urls import path
from . import views

app_name = 'markets'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Event sync API
    path('api/sync/', views.sync_events, name='sync_markets'),

    # Events API
    path('api/events/', views.get_events, name='get_events'),

    # Event matches API
    path('api/event-matches/create/', views.create_event_match, name='create_event_match'),
    path('api/event-matches/<int:match_id>/delete/', views.delete_event_match, name='delete_event_match'),
    path('api/event-matches/<int:match_id>/verify/', views.verify_event_match, name='verify_event_match'),
    path('api/refresh/', views.refresh_event_matches, name='refresh_arbitrage'),

    # Tags API
    path('api/tags/', views.get_tags, name='get_tags'),
    path('api/tags/refresh/', views.refresh_tags, name='refresh_tags'),
    path('api/tags/create/', views.create_tag, name='create_tag'),
    path('api/tags/<int:tag_id>/delete/', views.delete_tag, name='delete_tag'),

    # Tag matches API
    path('api/tag-matches/', views.get_tag_matches, name='get_tag_matches'),
    path('api/tag-matches/create/', views.create_tag_match, name='create_tag_match'),
    path('api/tag-matches/<int:match_id>/delete/', views.delete_tag_match, name='delete_tag_match'),
]
