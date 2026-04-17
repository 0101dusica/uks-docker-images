import logging

from django.conf import settings
from django.shortcuts import render
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError, TransportError

from users.permissions import admin_required
from .query_parser import parse_query, QueryParseError

logger = logging.getLogger(__name__)

LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


def build_es_query(date_from, date_to, level, text, parsed_query):
    """Build an Elasticsearch request body from the search form fields."""
    must = []

    if date_from or date_to:
        date_range = {}
        if date_from:
            date_range['gte'] = date_from
        if date_to:
            date_range['lte'] = date_to
        must.append({'range': {'asctime': date_range}})

    if level:
        must.append({'term': {'levelname': level.upper()}})

    if text:
        must.append({
            'multi_match': {
                'query': text,
                'fields': ['message', 'name'],
            }
        })

    if parsed_query:
        must.append(parsed_query)

    has_relevance_signal = bool(text or parsed_query)

    if not must:
        return {
            'query': {'match_all': {}},
            'sort': [{'asctime': {'order': 'desc'}}],
        }

    body = {'query': {'bool': {'must': must}}}

    # When text or a logical query is present sort by relevance score first,
    # otherwise just show newest logs at the top.
    if has_relevance_signal:
        body['sort'] = [
            {'_score': {'order': 'desc'}},
            {'asctime': {'order': 'desc'}},
        ]
    else:
        body['sort'] = [{'asctime': {'order': 'desc'}}]

    return body


@admin_required
def analytics_search_view(request):
    """Admin-only log search backed by Elasticsearch."""
    context = {
        'results': [],
        'total': 0,
        'error': None,
        'query_error': None,
        'date_from': '',
        'date_to': '',
        'level': '',
        'text': '',
        'query': '',
        'log_levels': LOG_LEVELS,
        'searched': False,
    }

    if request.method == 'POST':
        date_from = request.POST.get('date_from', '').strip()
        date_to   = request.POST.get('date_to', '').strip()
        level     = request.POST.get('level', '').strip()
        text      = request.POST.get('text', '').strip()
        query_str = request.POST.get('query', '').strip()

        context.update({
            'date_from': date_from,
            'date_to': date_to,
            'level': level,
            'text': text,
            'query': query_str,
            'searched': True,
        })

        # Validate the query syntax before hitting ES — bad input gets a yellow banner, not a 500.
        parsed_query = None
        if query_str:
            try:
                parsed_query = parse_query(query_str)
            except QueryParseError as exc:
                context['query_error'] = str(exc)
                return render(request, 'analytics_search.html', context)

        body = build_es_query(date_from, date_to, level, text, parsed_query)

        # size must go inside the body — passing it as a separate kwarg alongside body is deprecated in v8.
        body['size'] = 100

        try:
            es = Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=10)
            response = es.search(index='django-logs', body=body)

            hits = response['hits']['hits']
            total = response['hits']['total']['value']
            context['results'] = [h['_source'] for h in hits]
            context['total'] = total
            logger.info(
                "Analytics search executed",
                extra={
                    'admin_id': str(request.user.id),
                    'total_hits': total,
                    'level_filter': level,
                    'has_text': bool(text),
                    'has_query': bool(query_str),
                },
            )
        except (ESConnectionError, TransportError, Exception) as exc:
            # ES being down shouldn't crash the page, just show a banner.
            logger.warning("Elasticsearch unavailable during analytics search: %s", exc)
            context['error'] = "Elasticsearch is currently unavailable. Please try again later."

    return render(request, 'analytics_search.html', context)
