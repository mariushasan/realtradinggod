from django.urls import path
from . import views

app_name = 'markets'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('markets/', views.MarketsListView.as_view(), name='markets_list'),
    path('matches/', views.MatchesListView.as_view(), name='matches_list'),
    path('api/sync/', views.sync_markets, name='sync_markets'),
    path('api/tags/', views.get_tags, name='get_tags'),
    path('api/tags/refresh/', views.refresh_tags, name='refresh_tags'),
    path('api/tags/create/', views.create_tag, name='create_tag'),
    path('api/tags/<int:tag_id>/delete/', views.delete_tag, name='delete_tag'),
    path('api/tag-matches/', views.get_tag_matches, name='get_tag_matches'),
    path('api/tag-matches/create/', views.create_tag_match, name='create_tag_match'),
    path('api/tag-matches/<int:match_id>/delete/', views.delete_tag_match, name='delete_tag_match'),
    path('api/verify/<int:match_id>/', views.verify_match, name='verify_match'),
    path('api/refresh/', views.refresh_arbitrage, name='refresh_arbitrage'),
]
