from django.urls import path
from . import views

app_name = 'markets'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('markets/', views.MarketsListView.as_view(), name='markets_list'),
    path('matches/', views.MatchesListView.as_view(), name='matches_list'),
    path('api/sync/', views.sync_markets, name='sync_markets'),
    path('api/verify/<int:match_id>/', views.verify_match, name='verify_match'),
    path('api/refresh/', views.refresh_arbitrage, name='refresh_arbitrage'),
]
