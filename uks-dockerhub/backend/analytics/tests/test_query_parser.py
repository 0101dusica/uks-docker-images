from django.test import SimpleTestCase

from analytics.query_parser import parse_query, QueryParseError


class ParseQuerySimpleConditionsTests(SimpleTestCase):
    """Single-condition queries mapping to basic ES leaf clauses."""

    def test_level_eq_produces_term_on_levelname_uppercased(self):
        result = parse_query('level = warning')
        self.assertEqual(result, {'term': {'levelname': 'WARNING'}})

    def test_level_eq_already_uppercase(self):
        result = parse_query('level = ERROR')
        self.assertEqual(result, {'term': {'levelname': 'ERROR'}})

    def test_message_eq_produces_term(self):
        result = parse_query('message = hello')
        self.assertEqual(result, {'term': {'message': 'hello'}})

    def test_content_eq_maps_to_message_field(self):
        result = parse_query('content = failed')
        self.assertEqual(result, {'term': {'message': 'failed'}})

    def test_logger_eq_maps_to_name_field(self):
        result = parse_query('logger = myapp')
        self.assertEqual(result, {'term': {'name': 'myapp'}})

    def test_content_contains_produces_match(self):
        result = parse_query('content CONTAINS "error occurred"')
        self.assertEqual(result, {'match': {'message': 'error occurred'}})

    def test_message_contains_unquoted_word(self):
        result = parse_query('message CONTAINS failed')
        self.assertEqual(result, {'match': {'message': 'failed'}})

    def test_whitespace_around_tokens_is_ignored(self):
        result = parse_query('  level  =  debug  ')
        self.assertEqual(result, {'term': {'levelname': 'DEBUG'}})


class ParseQueryBooleanOperatorTests(SimpleTestCase):
    """Compound expressions using AND, OR, NOT."""

    def test_and_two_conditions(self):
        result = parse_query('level = ERROR AND content CONTAINS "fail"')
        self.assertEqual(result, {
            'bool': {
                'must': [
                    {'term': {'levelname': 'ERROR'}},
                    {'match': {'message': 'fail'}},
                ]
            }
        })

    def test_or_two_conditions(self):
        result = parse_query('level = WARNING OR level = ERROR')
        self.assertEqual(result, {
            'bool': {
                'should': [
                    {'term': {'levelname': 'WARNING'}},
                    {'term': {'levelname': 'ERROR'}},
                ],
                'minimum_should_match': 1,
            }
        })

    def test_not_wraps_in_must_not(self):
        result = parse_query('NOT level = DEBUG')
        self.assertEqual(result, {
            'bool': {'must_not': [{'term': {'levelname': 'DEBUG'}}]}
        })

    def test_not_not_double_negation(self):
        result = parse_query('NOT NOT level = ERROR')
        self.assertEqual(result, {
            'bool': {
                'must_not': [
                    {'bool': {'must_not': [{'term': {'levelname': 'ERROR'}}]}}
                ]
            }
        })

    def test_and_takes_precedence_over_or(self):
        # a OR b AND c  =>  a OR (b AND c)
        result = parse_query('level = INFO OR level = WARNING AND content CONTAINS "x"')
        self.assertEqual(result, {
            'bool': {
                'should': [
                    {'term': {'levelname': 'INFO'}},
                    {'bool': {'must': [
                        {'term': {'levelname': 'WARNING'}},
                        {'match': {'message': 'x'}},
                    ]}},
                ],
                'minimum_should_match': 1,
            }
        })

    def test_parentheses_override_precedence(self):
        # (a OR b) AND c
        result = parse_query('(level = INFO OR level = WARNING) AND content CONTAINS "x"')
        self.assertEqual(result, {
            'bool': {
                'must': [
                    {'bool': {
                        'should': [
                            {'term': {'levelname': 'INFO'}},
                            {'term': {'levelname': 'WARNING'}},
                        ],
                        'minimum_should_match': 1,
                    }},
                    {'match': {'message': 'x'}},
                ]
            }
        })

    def test_three_way_and(self):
        result = parse_query('level = ERROR AND logger = myapp AND content CONTAINS "db"')
        self.assertEqual(result, {
            'bool': {
                'must': [
                    {'term': {'levelname': 'ERROR'}},
                    {'term': {'name': 'myapp'}},
                    {'match': {'message': 'db'}},
                ]
            }
        })


class ParseQueryErrorTests(SimpleTestCase):
    """Invalid inputs that must raise QueryParseError."""

    def test_empty_string_raises(self):
        with self.assertRaises(QueryParseError):
            parse_query('')

    def test_whitespace_only_raises(self):
        with self.assertRaises(QueryParseError):
            parse_query('   ')

    def test_unknown_field_raises(self):
        with self.assertRaises(QueryParseError) as ctx:
            parse_query('severity = error')
        self.assertIn('severity', str(ctx.exception))

    def test_double_equals_raises(self):
        with self.assertRaises(QueryParseError):
            parse_query('level == error')

    def test_missing_value_after_eq_raises(self):
        with self.assertRaises(QueryParseError):
            parse_query('level =')

    def test_missing_closing_paren_raises(self):
        with self.assertRaises(QueryParseError):
            parse_query('(level = error')

    def test_unterminated_string_raises(self):
        with self.assertRaises(QueryParseError):
            parse_query('content CONTAINS "not closed')

    def test_unexpected_character_raises(self):
        with self.assertRaises(QueryParseError):
            parse_query('level @ error')

    def test_trailing_junk_raises(self):
        with self.assertRaises(QueryParseError):
            parse_query('level = error AND')
