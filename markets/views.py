import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from .models import Market, Event, EventMatch, MarketMatch, ArbitrageOpportunity, Exchange, Tag, TagMatch
from .services import EventMatcher, EventSyncService
from .api import PolymarketClient


class DashboardView(View):
    """Main dashboard showing events and matches"""
    ITEMS_PER_PAGE = 50

    def get(self, request):
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

        # Get event counts
        kalshi_event_count = Event.objects.filter(exchange=Exchange.KALSHI, is_active=True).count()
        poly_event_count = Event.objects.filter(exchange=Exchange.POLYMARKET, is_active=True).count()
        event_match_count = EventMatch.objects.count()

        # Get events for each exchange
        kalshi_events = Event.objects.filter(exchange=Exchange.KALSHI, is_active=True).order_by('-updated_at')[:100]
        poly_events = Event.objects.filter(exchange=Exchange.POLYMARKET, is_active=True).order_by('-updated_at')[:100]

        # Format events for template
        kalshi_events_list = [
            {
                'id': e.id,
                'external_id': e.external_id,
                'title': e.title,
                'url': e.url,
                'volume': e.volume,
                'liquidity': e.liquidity,
                'category': e.category,
                'end_date': e.end_date.isoformat() if e.end_date else None,
            }
            for e in kalshi_events
        ]

        poly_events_list = [
            {
                'id': e.id,
                'external_id': e.external_id,
                'title': e.title,
                'url': e.url,
                'volume': e.volume,
                'liquidity': e.liquidity,
                'category': e.category,
                'end_date': e.end_date.isoformat() if e.end_date else None,
            }
            for e in poly_events
        ]

        # Get event matches with pagination
        sort = request.GET.get('sort', '-similarity_score')
        valid_sorts = [
            'similarity_score', '-similarity_score',
            'is_verified', '-is_verified',
            'created_at', '-created_at'
        ]
        if sort not in valid_sorts:
            sort = '-similarity_score'

        page = request.GET.get('page', 1)

        event_matches = EventMatch.objects.select_related(
            'kalshi_event', 'polymarket_event'
        ).order_by(sort)

        # Pagination
        paginator = Paginator(event_matches, self.ITEMS_PER_PAGE)
        try:
            event_matches_page = paginator.page(page)
        except PageNotAnInteger:
            event_matches_page = paginator.page(1)
        except EmptyPage:
            event_matches_page = paginator.page(paginator.num_pages)

        context = {
            'kalshi_event_count': kalshi_event_count,
            'poly_event_count': poly_event_count,
            'event_match_count': event_match_count,
            'kalshi_tags_by_category': kalshi_tags_by_category,
            'polymarket_tags': polymarket_tags_list,
            'tag_matches': tag_matches_list,
            'tag_match_count': len(tag_matches_list),
            'kalshi_events': kalshi_events_list,
            'poly_events': poly_events_list,
            'event_matches': event_matches_page,
            'total_event_matches': paginator.count,
            'current_sort': sort,
        }

        return render(request, 'markets/dashboard.html', context)


@csrf_exempt
def sync_events(request):
    """Sync events from exchanges with optional tag and date filtering"""
    if request.method == 'POST':
        sync_service = EventSyncService()

        try:
            # Parse request body for filters
            kalshi_tag_slugs = None
            polymarket_tag_ids = None
            close_after = None
            close_before = None
            volume_min = None
            volume_max = None
            liquidity_min = None
            liquidity_max = None

            if request.body:
                try:
                    data = json.loads(request.body)
                    # Kalshi: list of tag slugs
                    kalshi_tags = data.get('kalshi_tags', [])
                    if kalshi_tags:
                        kalshi_tag_slugs = kalshi_tags

                    # Polymarket: list of tag IDs
                    poly_tags = data.get('polymarket_tags', [])
                    if poly_tags:
                        polymarket_tag_ids = [int(t) for t in poly_tags]

                    # Date filters (ISO format strings: YYYY-MM-DD)
                    close_after = data.get('close_after')
                    close_before = data.get('close_before')

                    # Volume/liquidity filters
                    if data.get('volume_min'):
                        volume_min = float(data.get('volume_min'))
                    if data.get('volume_max'):
                        volume_max = float(data.get('volume_max'))
                    if data.get('liquidity_min'):
                        liquidity_min = float(data.get('liquidity_min'))
                    if data.get('liquidity_max'):
                        liquidity_max = float(data.get('liquidity_max'))
                except (json.JSONDecodeError, ValueError):
                    pass

            results = sync_service.sync_all_events(
                kalshi_tag_slugs=kalshi_tag_slugs,
                polymarket_tag_ids=polymarket_tag_ids,
                close_after=close_after,
                close_before=close_before,
                volume_min=volume_min,
                volume_max=volume_max,
                liquidity_min=liquidity_min,
                liquidity_max=liquidity_max
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
def get_events(request):
    """Get events from database with optional search"""
    if request.method == 'GET':
        try:
            exchange = request.GET.get('exchange')
            search = request.GET.get('search', '').strip()
            limit = int(request.GET.get('limit', 100))

            events_qs = Event.objects.filter(is_active=True)

            if exchange:
                events_qs = events_qs.filter(exchange=exchange)

            if search:
                events_qs = events_qs.filter(
                    Q(title__icontains=search) | Q(description__icontains=search)
                )

            events_qs = events_qs.order_by('-updated_at')[:limit]

            events_list = [
                {
                    'id': e.id,
                    'exchange': e.exchange,
                    'external_id': e.external_id,
                    'title': e.title,
                    'url': e.url,
                    'volume': e.volume,
                    'liquidity': e.liquidity,
                    'category': e.category,
                    'end_date': e.end_date.isoformat() if e.end_date else None,
                }
                for e in events_qs
            ]

            return JsonResponse({
                'success': True,
                'events': events_list
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'GET required'}, status=405)


@csrf_exempt
def create_event_match(request):
    """Create a manual event match between a Kalshi event and a Polymarket event"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            kalshi_event_id = data.get('kalshi_event_id')
            polymarket_event_id = data.get('polymarket_event_id')

            if not kalshi_event_id or not polymarket_event_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Both kalshi_event_id and polymarket_event_id are required'
                }, status=400)

            # Get the events
            try:
                kalshi_event = Event.objects.get(id=kalshi_event_id, exchange=Exchange.KALSHI)
            except Event.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Kalshi event with id {kalshi_event_id} not found'
                }, status=404)

            try:
                polymarket_event = Event.objects.get(id=polymarket_event_id, exchange=Exchange.POLYMARKET)
            except Event.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Polymarket event with id {polymarket_event_id} not found'
                }, status=404)

            # Create or update the event match
            event_match, created = EventMatch.objects.update_or_create(
                kalshi_event=kalshi_event,
                polymarket_event=polymarket_event,
                defaults={
                    'similarity_score': 1.0,
                    'match_reason': "Manual match",
                }
            )

            return JsonResponse({
                'success': True,
                'created': created,
                'event_match': {
                    'id': event_match.id,
                    'kalshi_event': {
                        'id': kalshi_event.id,
                        'title': kalshi_event.title,
                        'url': kalshi_event.url,
                    },
                    'polymarket_event': {
                        'id': polymarket_event.id,
                        'title': polymarket_event.title,
                        'url': polymarket_event.url,
                    },
                    'similarity_score': event_match.similarity_score,
                    'match_reason': event_match.match_reason,
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
def delete_event_match(request, match_id):
    """Delete an event match"""
    if request.method == 'DELETE' or request.method == 'POST':
        try:
            event_match = get_object_or_404(EventMatch, id=match_id)
            event_match.delete()

            return JsonResponse({
                'success': True,
                'message': f'Event match {match_id} deleted'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'DELETE or POST required'}, status=405)


@csrf_exempt
def verify_event_match(request, match_id):
    """Verify/unverify an event match"""
    if request.method == 'POST':
        match = get_object_or_404(EventMatch, id=match_id)

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
def refresh_event_matches(request):
    """Semantically match events based on criteria filters"""
    if request.method == 'POST':
        try:
            # Parse request body for filters
            volume_min = None
            liquidity_min = None

            if request.body:
                try:
                    data = json.loads(request.body)
                    if data.get('volume_min'):
                        volume_min = float(data.get('volume_min'))
                    if data.get('liquidity_min'):
                        liquidity_min = float(data.get('liquidity_min'))
                except (json.JSONDecodeError, ValueError):
                    pass

            # Get events filtered by criteria
            kalshi_events_qs = Event.objects.filter(
                exchange=Exchange.KALSHI, is_active=True
            )
            poly_events_qs = Event.objects.filter(
                exchange=Exchange.POLYMARKET, is_active=True
            )

            if volume_min is not None:
                kalshi_events_qs = kalshi_events_qs.filter(volume__gte=volume_min)
                poly_events_qs = poly_events_qs.filter(volume__gte=volume_min)

            if liquidity_min is not None:
                kalshi_events_qs = kalshi_events_qs.filter(liquidity__gte=liquidity_min)
                poly_events_qs = poly_events_qs.filter(liquidity__gte=liquidity_min)

            kalshi_events = list(kalshi_events_qs)
            poly_events = list(poly_events_qs)

            # Run matching
            matcher = EventMatcher()
            matches = matcher.find_matches(kalshi_events, poly_events)
            matcher.create_match_records(matches)

            return JsonResponse({
                'success': True,
                'matches_found': len(matches),
                'kalshi_events_searched': len(kalshi_events),
                'polymarket_events_searched': len(poly_events),
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
    """Refresh tags from exchange APIs and save to database"""
    if request.method == 'POST':
        sync_service = EventSyncService()

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

            # Create or update the tag match
            tag_match, created = TagMatch.objects.update_or_create(
                kalshi_tag=kalshi_tag,
                polymarket_tag=polymarket_tag,
                defaults={
                    'similarity_score': 1.0,
                    'match_reason': f"Manual match",
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
def create_tag(request):
    """Create a manual tag for either exchange"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            exchange = data.get('exchange')
            label = data.get('label', '').strip()
            category = data.get('category', '').strip()
            external_id = data.get('external_id', '').strip()

            if not exchange or exchange not in [Exchange.KALSHI, Exchange.POLYMARKET]:
                return JsonResponse({
                    'success': False,
                    'error': 'Valid exchange (kalshi or polymarket) is required'
                }, status=400)

            if not label:
                return JsonResponse({
                    'success': False,
                    'error': 'Tag label is required'
                }, status=400)

            # Generate slug from label
            slug = label.lower().replace(' ', '-')

            # For Polymarket, generate a custom external_id if not provided
            if exchange == Exchange.POLYMARKET and not external_id:
                tag_data = PolymarketClient().get_tag_by_slug(slug)

                if not tag_data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Tag with slug {slug} not found'
                    }, status=404)

                external_id = tag_data.get('id')
                label = tag_data.get('label')
                slug = tag_data.get('slug')
                category = ''
            # Check if tag already exists
            existing = Tag.objects.filter(
                exchange=exchange,
                label=label,
                category=category
            ).first()

            if existing:
                return JsonResponse({
                    'success': False,
                    'error': f'Tag "{label}" already exists for {exchange}'
                }, status=400)

            tag = Tag.objects.create(
                exchange=exchange,
                label=label,
                slug=slug,
                category=category,
                external_id=external_id
            )

            return JsonResponse({
                'success': True,
                'tag': {
                    'id': tag.id,
                    'exchange': tag.exchange,
                    'label': tag.label,
                    'slug': tag.slug,
                    'category': tag.category,
                    'external_id': tag.external_id,
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
def delete_tag(request, tag_id):
    """Delete a tag"""
    if request.method == 'DELETE' or request.method == 'POST':
        try:
            tag = get_object_or_404(Tag, id=tag_id)
            label = tag.label
            exchange = tag.exchange
            tag.delete()

            return JsonResponse({
                'success': True,
                'message': f'Tag "{label}" deleted from {exchange}'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'DELETE or POST required'}, status=405)
