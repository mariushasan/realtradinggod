import json

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from .models import Event, EventMatch, Exchange
from .services import EventSyncService


def serialize_event(event, include_exchange=False):
    """Serialize an Event model instance to a dictionary"""
    data = {
        'id': event.id,
        'external_id': event.external_id,
        'title': event.title,
        'url': event.url,
        'volume': event.volume,
        'liquidity': event.liquidity,
        'category': event.category,
        'end_date': event.end_date.isoformat() if event.end_date else None,
    }
    if include_exchange:
        data['exchange'] = event.exchange
    return data


class DashboardView(View):
    """Main dashboard showing events and matches"""
    ITEMS_PER_PAGE = 50

    def get(self, request):
        # Get event counts
        kalshi_event_count = Event.objects.filter(exchange=Exchange.KALSHI, is_active=True).count()
        poly_event_count = Event.objects.filter(exchange=Exchange.POLYMARKET, is_active=True).count()
        event_match_count = EventMatch.objects.count()

        # Get events for each exchange
        kalshi_events = Event.objects.filter(exchange=Exchange.KALSHI, is_active=True).order_by('-updated_at')[:100]
        poly_events = Event.objects.filter(exchange=Exchange.POLYMARKET, is_active=True).order_by('-updated_at')[:100]

        # Get event matches with pagination
        sort = request.GET.get('sort', '-similarity_score')
        valid_sorts = ['similarity_score', '-similarity_score', 'is_verified', '-is_verified', 'created_at', '-created_at']
        if sort not in valid_sorts:
            sort = '-similarity_score'

        page = request.GET.get('page', 1)
        event_matches = EventMatch.objects.select_related('kalshi_event', 'polymarket_event').order_by(sort)

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
            'kalshi_events': [serialize_event(e) for e in kalshi_events],
            'poly_events': [serialize_event(e) for e in poly_events],
            'event_matches': event_matches_page,
            'total_event_matches': paginator.count,
            'current_sort': sort,
        }

        return render(request, 'markets/dashboard.html', context)


@csrf_exempt
def sync_events(request):
    """Sync events from exchanges with optional date filtering"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        close_after = None
        if request.body:
            try:
                data = json.loads(request.body)
                close_after = data.get('close_after')
            except (json.JSONDecodeError, ValueError):
                pass

        sync_service = EventSyncService()
        results = sync_service.sync_all_events(close_after=close_after)

        return JsonResponse({
            'success': True,
            'kalshi_synced': len(results['kalshi']),
            'polymarket_synced': len(results['polymarket']),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def get_events(request):
    """Get events from database with optional search"""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)

    try:
        exchange = request.GET.get('exchange')
        search = request.GET.get('search', '').strip()
        limit = int(request.GET.get('limit', 100))

        events_qs = Event.objects.filter(is_active=True)

        if exchange:
            events_qs = events_qs.filter(exchange=exchange)

        if search:
            events_qs = events_qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        events_qs = events_qs.order_by('-updated_at')[:limit]

        return JsonResponse({
            'success': True,
            'events': [serialize_event(e, include_exchange=True) for e in events_qs]
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def create_event_match(request):
    """Create a manual event match between a Kalshi event and a Polymarket event"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        kalshi_event_id = data.get('kalshi_event_id')
        polymarket_event_id = data.get('polymarket_event_id')

        if not kalshi_event_id or not polymarket_event_id:
            return JsonResponse({
                'success': False,
                'error': 'Both kalshi_event_id and polymarket_event_id are required'
            }, status=400)

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

        event_match, created = EventMatch.objects.update_or_create(
            kalshi_event=kalshi_event,
            polymarket_event=polymarket_event,
            defaults={'similarity_score': 1.0, 'match_reason': "Manual match"}
        )

        return JsonResponse({
            'success': True,
            'created': created,
            'event_match': {
                'id': event_match.id,
                'kalshi_event': {'id': kalshi_event.id, 'title': kalshi_event.title, 'url': kalshi_event.url},
                'polymarket_event': {'id': polymarket_event.id, 'title': polymarket_event.title, 'url': polymarket_event.url},
                'similarity_score': event_match.similarity_score,
                'match_reason': event_match.match_reason,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def delete_event_match(request, match_id):
    """Delete an event match"""
    if request.method not in ('DELETE', 'POST'):
        return JsonResponse({'error': 'DELETE or POST required'}, status=405)

    try:
        event_match = get_object_or_404(EventMatch, id=match_id)
        event_match.delete()
        return JsonResponse({'success': True, 'message': f'Event match {match_id} deleted'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def verify_event_match(request, match_id):
    """Verify/unverify an event match"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    match = get_object_or_404(EventMatch, id=match_id)
    match.is_verified = not match.is_verified
    match.verified_at = timezone.now() if match.is_verified else None
    match.save()

    return JsonResponse({
        'success': True,
        'is_verified': match.is_verified,
        'verified_at': match.verified_at.isoformat() if match.verified_at else None
    })
