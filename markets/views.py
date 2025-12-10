from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import Market, MarketMatch, ArbitrageOpportunity, Exchange
from .services import MarketMatcher, ArbitrageDetector, MarketSyncService


class DashboardView(View):
    """Main dashboard showing arbitrage opportunities"""

    def get(self, request):
        # Get active arbitrage opportunities
        opportunities = ArbitrageOpportunity.objects.filter(
            is_active=True
        ).select_related('market_match').prefetch_related('markets')

        # Separate by type
        kalshi_only = opportunities.filter(arb_type=ArbitrageOpportunity.ArbitrageType.KALSHI_ONLY)
        poly_only = opportunities.filter(arb_type=ArbitrageOpportunity.ArbitrageType.POLYMARKET_ONLY)
        cross_exchange = opportunities.filter(arb_type=ArbitrageOpportunity.ArbitrageType.CROSS_EXCHANGE)

        # Get market counts
        kalshi_count = Market.objects.filter(exchange=Exchange.KALSHI, is_active=True).count()
        poly_count = Market.objects.filter(exchange=Exchange.POLYMARKET, is_active=True).count()
        match_count = MarketMatch.objects.count()

        context = {
            'kalshi_only': kalshi_only,
            'poly_only': poly_only,
            'cross_exchange': cross_exchange,
            'total_opportunities': opportunities.count(),
            'kalshi_count': kalshi_count,
            'poly_count': poly_count,
            'match_count': match_count,
        }

        return render(request, 'markets/dashboard.html', context)


class MarketsListView(View):
    """List all markets"""

    def get(self, request):
        exchange_filter = request.GET.get('exchange', '')

        markets = Market.objects.filter(is_active=True)

        if exchange_filter:
            markets = markets.filter(exchange=exchange_filter)

        markets = markets.order_by('-updated_at')[:100]

        context = {
            'markets': markets,
            'exchange_filter': exchange_filter,
            'exchanges': Exchange.choices
        }

        return render(request, 'markets/markets_list.html', context)


class MatchesListView(View):
    """List all market matches"""

    def get(self, request):
        verified_filter = request.GET.get('verified', '')

        matches = MarketMatch.objects.select_related(
            'kalshi_market', 'polymarket_market'
        ).order_by('-similarity_score')

        if verified_filter == 'true':
            matches = matches.filter(is_verified=True)
        elif verified_filter == 'false':
            matches = matches.filter(is_verified=False)

        context = {
            'matches': matches,
            'verified_filter': verified_filter
        }

        return render(request, 'markets/matches_list.html', context)


@csrf_exempt
def sync_markets(request):
    """Sync markets from exchanges"""
    if request.method == 'POST':
        sync_service = MarketSyncService()

        try:
            results = sync_service.sync_all()

            # Run matching after sync
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
                'kalshi_synced': len(results['kalshi']),
                'polymarket_synced': len(results['polymarket']),
                'matches_found': len(matches),
                'opportunities_found': len(opportunities)
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
    """Refresh arbitrage detection only"""
    if request.method == 'POST':
        try:
            detector = ArbitrageDetector()
            opportunities = detector.find_all_opportunities()
            detector.save_opportunities(opportunities)

            return JsonResponse({
                'success': True,
                'opportunities_found': len(opportunities)
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'POST required'}, status=405)
