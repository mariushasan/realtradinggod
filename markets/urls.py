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

    # Event matches API (for manual matching)
    path('api/event-matches/create/', views.create_event_match, name='create_event_match'),
    path('api/event-matches/<int:match_id>/delete/', views.delete_event_match, name='delete_event_match'),
    path('api/event-matches/<int:match_id>/verify/', views.verify_event_match, name='verify_event_match'),
]
