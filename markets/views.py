from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Market, MarketMatch, ArbitrageOpportunity, Exchange
from .services import MarketMatcher, ArbitrageDetector, MarketSyncService


class DashboardView(View):
    """Main dashboard showing arbitrage opportunities"""
    ITEMS_PER_PAGE = 50

    def get(self, request):
        # Sorting
        sort = request.GET.get('sort', '-profit_percent')
        valid_sorts = [
            'profit_percent', '-profit_percent',
            'expected_value', '-expected_value',
            'arb_type', '-arb_type',
            'updated_at', '-updated_at'
        ]
        if sort not in valid_sorts:
            sort = '-profit_percent'

        page = request.GET.get('page', 1)

        # Get all active arbitrage opportunities (mixed)
        opportunities = ArbitrageOpportunity.objects.filter(
            is_active=True
        ).select_related('market_match', 'market_match__kalshi_market', 'market_match__polymarket_market').prefetch_related('markets').order_by(sort)

        # Pagination
        paginator = Paginator(opportunities, self.ITEMS_PER_PAGE)
        try:
            opportunities_page = paginator.page(page)
        except PageNotAnInteger:
            opportunities_page = paginator.page(1)
        except EmptyPage:
            opportunities_page = paginator.page(paginator.num_pages)

        # Get market counts
        kalshi_count = Market.objects.filter(exchange=Exchange.KALSHI, is_active=True).count()
        poly_count = Market.objects.filter(exchange=Exchange.POLYMARKET, is_active=True).count()
        match_count = MarketMatch.objects.count()

        context = {
            'opportunities': opportunities_page,
            'total_opportunities': paginator.count,
            'kalshi_count': kalshi_count,
            'poly_count': poly_count,
            'match_count': match_count,
            'current_sort': sort,
        }

        return render(request, 'markets/dashboard.html', context)


class MarketsListView(View):
    """List all markets with pagination and sorting"""
    ITEMS_PER_PAGE = 50

    def get(self, request):
        exchange_filter = request.GET.get('exchange', '')
        sort = request.GET.get('sort', '-updated_at')
        page = request.GET.get('page', 1)

        # Valid sort options
        valid_sorts = ['title', '-title', 'updated_at', '-updated_at', 'exchange', '-exchange']
        if sort not in valid_sorts:
            sort = '-updated_at'

        markets = Market.objects.filter(is_active=True)

        if exchange_filter:
            markets = markets.filter(exchange=exchange_filter)

        markets = markets.order_by(sort)

        # Pagination
        paginator = Paginator(markets, self.ITEMS_PER_PAGE)
        try:
            markets_page = paginator.page(page)
        except PageNotAnInteger:
            markets_page = paginator.page(1)
        except EmptyPage:
            markets_page = paginator.page(paginator.num_pages)

        context = {
            'markets': markets_page,
            'exchange_filter': exchange_filter,
            'exchanges': Exchange.choices,
            'current_sort': sort,
            'total_count': paginator.count,
        }

        return render(request, 'markets/markets_list.html', context)


class MatchesListView(View):
    """List all market matches with pagination and sorting"""
    ITEMS_PER_PAGE = 25

    def get(self, request):
        verified_filter = request.GET.get('verified', '')
        sort = request.GET.get('sort', '-similarity_score')
        page = request.GET.get('page', 1)

        # Valid sort options
        valid_sorts = [
            'similarity_score', '-similarity_score',
            'is_verified', '-is_verified',
            'created_at', '-created_at'
        ]
        if sort not in valid_sorts:
            sort = '-similarity_score'

        matches = MarketMatch.objects.select_related(
            'kalshi_market', 'polymarket_market'
        ).order_by(sort)

        if verified_filter == 'true':
            matches = matches.filter(is_verified=True)
        elif verified_filter == 'false':
            matches = matches.filter(is_verified=False)

        # Pagination
        paginator = Paginator(matches, self.ITEMS_PER_PAGE)
        try:
            matches_page = paginator.page(page)
        except PageNotAnInteger:
            matches_page = paginator.page(1)
        except EmptyPage:
            matches_page = paginator.page(paginator.num_pages)

        context = {
            'matches': matches_page,
            'verified_filter': verified_filter,
            'current_sort': sort,
            'total_count': paginator.count,
        }

        return render(request, 'markets/matches_list.html', context)


@csrf_exempt
def sync_markets(request):
    """Sync markets from exchanges (fetch and save only)"""
    if request.method == 'POST':
        sync_service = MarketSyncService()

        try:
            results = sync_service.sync_all()

            return JsonResponse({
                'success': True,
                'kalshi_synced': len(results['kalshi']),
                'polymarket_synced': len(results['polymarket']),
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'POST required'}, status=405)


@csrf_exempt
def verify_match(request, match_id):
    """Verify/unverify a market match"""
    if request.method == 'POST':
        match = get_object_or_404(MarketMatch, id=match_id)

        # Toggle verification
        match.is_verified = not match.is_verified
        if match.is_verified:
            match.verified_at = timezone.now()
        else:
            match.verified_at = None
        match.save()

        return JsonResponse({
            'success': True,
            'is_verified': match.is_verified,
            'verified_at': match.verified_at.isoformat() if match.verified_at else None
        })

    return JsonResponse({'error': 'POST required'}, status=405)


@csrf_exempt
def refresh_arbitrage(request):
    """Refresh matching and arbitrage detection"""
    if request.method == 'POST':
        try:
            # Run matching
            matcher = MarketMatcher()
            kalshi_markets = list(Market.objects.filter(
                exchange=Exchange.KALSHI, is_active=True
            ))
            poly_markets = list(Market.objects.filter(
                exchange=Exchange.POLYMARKET, is_active=True
            ))

            matches = matcher.find_matches(kalshi_markets, poly_markets)
            matcher.create_match_records(matches)

            # Detect arbitrage
            detector = ArbitrageDetector()
            opportunities = detector.find_all_opportunities()
            detector.save_opportunities(opportunities)

            return JsonResponse({
                'success': True,
                'matches_found': len(matches),
                'opportunities_found': len(opportunities)
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'POST required'}, status=405)
