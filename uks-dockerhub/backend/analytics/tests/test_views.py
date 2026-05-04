from unittest.mock import MagicMock, patch

from django.test import TestCase, Client
from django.urls import reverse

from analytics.views import build_es_query
from users.models import User


class BuildEsQueryTests(TestCase):
    """Unit tests for the build_es_query helper - no HTTP, no ES."""

    def test_no_filters_returns_match_all_sorted_by_asctime(self):
        body = build_es_query('', '', '', '', None)
        self.assertEqual(body['query'], {'match_all': {}})
        self.assertEqual(body['sort'], [{'asctime': {'order': 'desc'}}])

    def test_level_filter_adds_term_clause(self):
        body = build_es_query('', '', 'ERROR', '', None)
        must = body['query']['bool']['must']
        self.assertIn({'term': {'levelname': 'ERROR'}}, must)

    def test_level_is_uppercased(self):
        body = build_es_query('', '', 'warning', '', None)
        must = body['query']['bool']['must']
        self.assertIn({'term': {'levelname': 'WARNING'}}, must)

    def test_text_filter_adds_multi_match(self):
        body = build_es_query('', '', '', 'login failed', None)
        must = body['query']['bool']['must']
        self.assertTrue(
            any('multi_match' in c for c in must),
            msg='Expected a multi_match clause for text filter',
        )

    def test_date_from_adds_range_gte(self):
        body = build_es_query('2026-01-01T00:00', '', '', '', None)
        must = body['query']['bool']['must']
        self.assertIn({'range': {'asctime': {'gte': '2026-01-01T00:00'}}}, must)

    def test_date_to_adds_range_lte(self):
        body = build_es_query('', '2026-12-31T23:59', '', '', None)
        must = body['query']['bool']['must']
        self.assertIn({'range': {'asctime': {'lte': '2026-12-31T23:59'}}}, must)

    def test_date_range_both_bounds(self):
        body = build_es_query('2026-01-01T00:00', '2026-12-31T23:59', '', '', None)
        must = body['query']['bool']['must']
        self.assertIn(
            {'range': {'asctime': {'gte': '2026-01-01T00:00', 'lte': '2026-12-31T23:59'}}},
            must,
        )

    def test_parsed_query_is_appended_to_must(self):
        parsed = {'term': {'levelname': 'ERROR'}}
        body = build_es_query('', '', '', '', parsed)
        self.assertIn(parsed, body['query']['bool']['must'])

    def test_text_triggers_score_sort(self):
        body = build_es_query('', '', '', 'crash', None)
        self.assertEqual(body['sort'][0], {'_score': {'order': 'desc'}})
        self.assertEqual(body['sort'][1], {'asctime': {'order': 'desc'}})

    def test_parsed_query_triggers_score_sort(self):
        parsed = {'term': {'levelname': 'ERROR'}}
        body = build_es_query('', '', '', '', parsed)
        self.assertEqual(body['sort'][0], {'_score': {'order': 'desc'}})

    def test_level_only_uses_asctime_sort(self):
        body = build_es_query('', '', 'INFO', '', None)
        self.assertEqual(body['sort'], [{'asctime': {'order': 'desc'}}])


class AnalyticsSearchViewTests(TestCase):
    """Integration tests for the analytics search view."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='adminpass123',
            role='admin',
        )
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='userpass123',
            role='user',
        )
        self.url = reverse('analytics-search')

    # ------------------------------------------------------------------ access

    def test_unauthenticated_user_gets_403(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_regular_user_gets_403(self):
        self.client.login(username='testuser', password='userpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_admin_get_returns_200(self):
        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_renders_correct_template(self):
        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'analytics_search.html')

    def test_get_does_not_set_searched_flag(self):
        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.get(self.url)
        self.assertFalse(response.context['searched'])

    # ------------------------------------------------------------------ POST with mocked ES

    def _make_es_response(self, hits=None, total=0):
        hit_list = hits or []
        mock_resp = {
            'hits': {
                'hits': [{'_source': h} for h in hit_list],
                'total': {'value': total},
            }
        }
        return mock_resp

    @patch('analytics.views.Elasticsearch')
    def test_post_empty_form_calls_es_and_renders_results(self, MockES):
        mock_es = MagicMock()
        MockES.return_value = mock_es
        mock_es.search.return_value = self._make_es_response(
            hits=[{'asctime': '2026-01-01', 'levelname': 'INFO',
                   'name': 'myapp', 'message': 'started'}],
            total=1,
        )

        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['searched'])
        self.assertEqual(response.context['total'], 1)
        self.assertEqual(len(response.context['results']), 1)

    @patch('analytics.views.Elasticsearch')
    def test_post_level_filter_passed_to_es(self, MockES):
        mock_es = MagicMock()
        MockES.return_value = mock_es
        mock_es.search.return_value = self._make_es_response()

        self.client.login(username='testadmin', password='adminpass123')
        self.client.post(self.url, {'level': 'ERROR'})

        # search is called twice: first for dashboard stats, then for the actual query.
        # call_args returns the last call, which is the log search.
        call_kwargs = mock_es.search.call_args
        body = call_kwargs.kwargs.get('body') or call_kwargs[1].get('body')
        must = body['query']['bool']['must']
        self.assertIn({'term': {'levelname': 'ERROR'}}, must)

    @patch('analytics.views.Elasticsearch')
    def test_post_invalid_query_returns_query_error_no_es_call(self, MockES):
        mock_es = MagicMock()
        MockES.return_value = mock_es
        mock_es.search.return_value = self._make_es_response()

        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.post(self.url, {'query': 'level =='})

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['query_error'])
        # ES client is created for stats, but the actual log search must not run.
        mock_es.search.assert_called_once()

    @patch('analytics.views.Elasticsearch')
    def test_post_es_unavailable_sets_error_context(self, MockES):
        from elasticsearch.exceptions import ConnectionError as ESConnectionError
        mock_es = MagicMock()
        MockES.return_value = mock_es
        mock_es.search.side_effect = ESConnectionError('ES down')

        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['error'])
        self.assertEqual(response.context['results'], [])

    @patch('analytics.views.Elasticsearch')
    def test_post_repopulates_form_fields_on_rerender(self, MockES):
        mock_es = MagicMock()
        MockES.return_value = mock_es
        mock_es.search.return_value = self._make_es_response()

        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.post(self.url, {
            'level': 'WARNING',
            'text': 'login',
            'date_from': '2026-01-01T00:00',
            'date_to': '2026-12-31T23:59',
        })

        self.assertEqual(response.context['level'], 'WARNING')
        self.assertEqual(response.context['text'], 'login')
        self.assertEqual(response.context['date_from'], '2026-01-01T00:00')
        self.assertEqual(response.context['date_to'], '2026-12-31T23:59')

    @patch('analytics.views.Elasticsearch')
    def test_get_stats_populated_when_es_available(self, MockES):
        mock_es = MagicMock()
        MockES.return_value = mock_es
        mock_es.search.return_value = {
            'hits': {'total': {'value': 42}},
            'aggregations': {
                'by_level': {
                    'buckets': [
                        {'key': 'INFO', 'doc_count': 30},
                        {'key': 'ERROR', 'doc_count': 12},
                    ]
                }
            },
        }

        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.get(self.url)

        stats = response.context['stats']
        self.assertIsNotNone(stats)
        self.assertEqual(stats['total'], 42)
        self.assertEqual(stats['by_level']['INFO'], 30)
        self.assertEqual(stats['by_level']['ERROR'], 12)

    @patch('analytics.views.Elasticsearch')
    def test_get_stats_none_when_es_unavailable(self, MockES):
        mock_es = MagicMock()
        MockES.return_value = mock_es
        mock_es.search.side_effect = Exception('ES down')

        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.get(self.url)

        self.assertIsNone(response.context['stats'])
        self.assertEqual(response.status_code, 200)

    @patch('analytics.views.Elasticsearch')
    def test_post_no_results_sets_empty_list(self, MockES):
        mock_es = MagicMock()
        MockES.return_value = mock_es
        mock_es.search.return_value = self._make_es_response(total=0)

        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.post(self.url, {'level': 'CRITICAL'})

        self.assertEqual(response.context['results'], [])
        self.assertEqual(response.context['total'], 0)
        self.assertTrue(response.context['searched'])
