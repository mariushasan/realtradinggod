import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Market, MarketMatch, ArbitrageOpportunity, Exchange, Tag, TagMatch
from .services import MarketMatcher, TagMatcher, ArbitrageDetector, MarketSyncService


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

        # Get tags for the filter UI
        kalshi_tags = Tag.objects.filter(exchange=Exchange.KALSHI).order_by('category', 'label')
        polymarket_tags = Tag.objects.filter(exchange=Exchange.POLYMARKET).order_by('label')

        # Group Kalshi tags by category for template
        kalshi_tags_by_category = {}
        for tag in kalshi_tags:
            category = tag.category or 'Other'
            if category not in kalshi_tags_by_category:
                kalshi_tags_by_category[category] = []
            kalshi_tags_by_category[category].append({
                'id': tag.id,
                'label': tag.label,
                'slug': tag.slug,
            })

        # Format Polymarket tags
        polymarket_tags_list = [
            {'id': tag.id, 'external_id': tag.external_id, 'label': tag.label, 'slug': tag.slug}
            for tag in polymarket_tags
        ]

        # Get tag matches for the matched tags section
        tag_matches = TagMatch.objects.select_related(
            'kalshi_tag', 'polymarket_tag'
        ).order_by('-similarity_score')

        tag_matches_list = [
            {
                'id': tm.id,
                'kalshi_tag': {
                    'id': tm.kalshi_tag.id,
                    'label': tm.kalshi_tag.label,
                    'slug': tm.kalshi_tag.slug,
                    'category': tm.kalshi_tag.category,
                },
                'polymarket_tag': {
                    'id': tm.polymarket_tag.id,
                    'external_id': tm.polymarket_tag.external_id,
                    'label': tm.polymarket_tag.label,
                    'slug': tm.polymarket_tag.slug,
                },
                'similarity_score': tm.similarity_score,
                'match_reason': tm.match_reason,
                'is_manual': tm.is_manual,
            }
            for tm in tag_matches
        ]

        context = {
            'opportunities': opportunities_page,
            'total_opportunities': paginator.count,
            'kalshi_count': kalshi_count,
            'poly_count': poly_count,
            'match_count': match_count,
            'current_sort': sort,
            'kalshi_tags_by_category': kalshi_tags_by_category,
            'polymarket_tags': polymarket_tags_list,
            'tag_matches': tag_matches_list,
            'tag_match_count': len(tag_matches_list),
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
    """Sync markets from exchanges (fetch and save only), with optional tag filtering"""
    if request.method == 'POST':
        sync_service = MarketSyncService()

        try:
            # Parse request body for tag filters
            kalshi_tag_slugs = None
            polymarket_tag_ids = None

            if request.body:
                try:
                    data = json.loads(request.body)
                    # Kalshi: list of tag slugs (used to get categories, then series, then markets)
                    kalshi_tags = data.get('kalshi_tags', [])
                    if kalshi_tags:
                        kalshi_tag_slugs = kalshi_tags

                    # Polymarket: list of tag IDs
                    poly_tags = data.get('polymarket_tags', [])
                    if poly_tags:
                        polymarket_tag_ids = [int(t) for t in poly_tags]
                except (json.JSONDecodeError, ValueError):
                    pass

            results = sync_service.sync_all(
                kalshi_tag_slugs=kalshi_tag_slugs,
                polymarket_tag_ids=polymarket_tag_ids
            )

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
def get_tags(request):
    """Get available tags from database"""
    if request.method == 'GET':
        try:
            # Get tags from database
            kalshi_tags = Tag.objects.filter(exchange=Exchange.KALSHI).order_by('category', 'label')
            polymarket_tags = Tag.objects.filter(exchange=Exchange.POLYMARKET).order_by('label')

            # Format Kalshi tags
            kalshi_formatted = []
            for tag in kalshi_tags:
                kalshi_formatted.append({
                    'id': tag.id,
                    'label': tag.label,
                    'slug': tag.slug,
                    'category': tag.category,
                })

            # Format Polymarket tags
            polymarket_formatted = []
            for tag in polymarket_tags:
                polymarket_formatted.append({
                    'id': tag.id,
                    'external_id': tag.external_id,
                    'label': tag.label,
                    'slug': tag.slug,
                })

            return JsonResponse({
                'success': True,
                'kalshi': kalshi_formatted,
                'polymarket': polymarket_formatted
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'GET required'}, status=405)


@csrf_exempt
def refresh_tags(request):
    """Refresh tags from exchange APIs, save to database, and find tag matches"""
    if request.method == 'POST':
        sync_service = MarketSyncService()

        try:
            results = sync_service.sync_all_tags(auto_match=True)

            return JsonResponse({
                'success': True,
                'kalshi_synced': len(results['kalshi']),
                'polymarket_synced': len(results['polymarket']),
                'tag_matches_found': len(results.get('tag_matches', [])),
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'POST required'}, status=405)


@csrf_exempt
def get_tag_matches(request):
    """Get all tag matches from database"""
    if request.method == 'GET':
        try:
            tag_matches = TagMatch.objects.select_related(
                'kalshi_tag', 'polymarket_tag'
            ).order_by('-similarity_score')

            matches_list = []
            for tm in tag_matches:
                matches_list.append({
                    'id': tm.id,
                    'kalshi_tag': {
                        'id': tm.kalshi_tag.id,
                        'label': tm.kalshi_tag.label,
                        'slug': tm.kalshi_tag.slug,
                        'category': tm.kalshi_tag.category,
                    },
                    'polymarket_tag': {
                        'id': tm.polymarket_tag.id,
                        'external_id': tm.polymarket_tag.external_id,
                        'label': tm.polymarket_tag.label,
                        'slug': tm.polymarket_tag.slug,
                    },
                    'similarity_score': tm.similarity_score,
                    'match_reason': tm.match_reason,
                    'is_manual': tm.is_manual,
                })

            return JsonResponse({
                'success': True,
                'tag_matches': matches_list
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'GET required'}, status=405)


@csrf_exempt
def create_tag_match(request):
    """Create a manual tag match between a Kalshi tag and a Polymarket tag"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            kalshi_tag_id = data.get('kalshi_tag_id')
            polymarket_tag_id = data.get('polymarket_tag_id')

            if not kalshi_tag_id or not polymarket_tag_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Both kalshi_tag_id and polymarket_tag_id are required'
                }, status=400)

            # Get the tags
            try:
                kalshi_tag = Tag.objects.get(id=kalshi_tag_id, exchange=Exchange.KALSHI)
            except Tag.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Kalshi tag with id {kalshi_tag_id} not found'
                }, status=404)

            try:
                polymarket_tag = Tag.objects.get(id=polymarket_tag_id, exchange=Exchange.POLYMARKET)
            except Tag.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Polymarket tag with id {polymarket_tag_id} not found'
                }, status=404)

            # Calculate similarity score for the manual match
            tag_matcher = TagMatcher()
            kalshi_text = kalshi_tag.label
            if kalshi_tag.category:
                kalshi_text = f"{kalshi_tag.category} {kalshi_tag.label}"

            score, breakdown = tag_matcher.compute_tag_similarity(
                kalshi_text,
                polymarket_tag.label
            )
            reason = tag_matcher.generate_tag_match_reason(breakdown)

            # Create or update the tag match
            tag_match, created = TagMatch.objects.update_or_create(
                kalshi_tag=kalshi_tag,
                polymarket_tag=polymarket_tag,
                defaults={
                    'similarity_score': score,
                    'match_reason': f"Manual match | {reason}",
                    'is_manual': True
                }
            )

            return JsonResponse({
                'success': True,
                'created': created,
                'tag_match': {
                    'id': tag_match.id,
                    'kalshi_tag': {
                        'id': kalshi_tag.id,
                        'label': kalshi_tag.label,
                        'slug': kalshi_tag.slug,
                        'category': kalshi_tag.category,
                    },
                    'polymarket_tag': {
                        'id': polymarket_tag.id,
                        'external_id': polymarket_tag.external_id,
                        'label': polymarket_tag.label,
                        'slug': polymarket_tag.slug,
                    },
                    'similarity_score': tag_match.similarity_score,
                    'match_reason': tag_match.match_reason,
                    'is_manual': tag_match.is_manual,
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON in request body'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'POST required'}, status=405)


@csrf_exempt
def delete_tag_match(request, match_id):
    """Delete a tag match"""
    if request.method == 'DELETE' or request.method == 'POST':
        try:
            tag_match = get_object_or_404(TagMatch, id=match_id)
            tag_match.delete()

            return JsonResponse({
                'success': True,
                'message': f'Tag match {match_id} deleted'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'DELETE or POST required'}, status=405)


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
    """Refresh matching and arbitrage detection, filtered by selected tags"""
    if request.method == 'POST':
        try:
            # Parse request body for tag filters
            kalshi_tag_slugs = []
            polymarket_tag_ids = []

            if request.body:
                try:
                    data = json.loads(request.body)
                    kalshi_tag_slugs = data.get('kalshi_tags', [])
                    poly_tags = data.get('polymarket_tags', [])
                    if poly_tags:
                        polymarket_tag_ids = [str(t) for t in poly_tags]
                except (json.JSONDecodeError, ValueError):
                    pass

            # Filter markets by tags if specified
            kalshi_markets_qs = Market.objects.filter(
                exchange=Exchange.KALSHI, is_active=True
            )
            poly_markets_qs = Market.objects.filter(
                exchange=Exchange.POLYMARKET, is_active=True
            )

            if kalshi_tag_slugs:
                kalshi_markets_qs = kalshi_markets_qs.filter(
                    tags__slug__in=kalshi_tag_slugs
                ).distinct()

            if polymarket_tag_ids:
                poly_markets_qs = poly_markets_qs.filter(
                    tags__external_id__in=polymarket_tag_ids
                ).distinct()

            kalshi_markets = list(kalshi_markets_qs)
            poly_markets = list(poly_markets_qs)

            # Run matching
            matcher = MarketMatcher()
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
