"""
Recursive descent parser for the analytics logical query language.

Grammar:
    expr     := or_expr
    or_expr  := and_expr ('OR' and_expr)*
    and_expr := not_expr ('AND' not_expr)*
    not_expr := 'NOT' not_expr | atom
    atom     := '(' expr ')' | condition
    condition := WORD ('=' | 'CONTAINS') (WORD | STRING)

Example:
    (level = warning OR level = error) AND content CONTAINS "error occurred"
"""

from dataclasses import dataclass
from typing import List, Optional


class QueryParseError(Exception):
    pass


# ------------------------------------------------------------------ token types

TOK_LPAREN   = 'LPAREN'
TOK_RPAREN   = 'RPAREN'
TOK_AND      = 'AND'
TOK_OR       = 'OR'
TOK_NOT      = 'NOT'
TOK_EQ       = 'EQ'
TOK_CONTAINS = 'CONTAINS'
TOK_STRING   = 'STRING'
TOK_WORD     = 'WORD'
TOK_EOF      = 'EOF'

_KEYWORDS = {'AND', 'OR', 'NOT', 'CONTAINS'}

# Maps query field names to Elasticsearch document field names.
_FIELD_MAP = {
    'level':   'levelname',
    'message': 'message',
    'content': 'message',
    'logger':  'name',
}


@dataclass
class Token:
    type: str
    value: str


# ------------------------------------------------------------------ tokenizer

def tokenize(text: str) -> List[Token]:
    """Convert a raw query string into a flat list of tokens."""
    tokens: List[Token] = []
    i = 0
    n = len(text)

    while i < n:
        c = text[i]

        if c.isspace():
            i += 1

        elif c == '(':
            tokens.append(Token(TOK_LPAREN, '('))
            i += 1

        elif c == ')':
            tokens.append(Token(TOK_RPAREN, ')'))
            i += 1

        elif c == '=':
            tokens.append(Token(TOK_EQ, '='))
            i += 1

        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 1
            if j >= n:
                raise QueryParseError("Unterminated string literal — missing closing '\"'")
            tokens.append(Token(TOK_STRING, text[i + 1:j]))
            i = j + 1

        elif c.isalnum() or c in ('_', '-', '.'):
            j = i
            while j < n and (text[j].isalnum() or text[j] in ('_', '-', '.')):
                j += 1
            word = text[i:j]
            upper = word.upper()
            if upper in _KEYWORDS:
                tokens.append(Token(upper, word))
            else:
                tokens.append(Token(TOK_WORD, word))
            i = j

        else:
            raise QueryParseError(f"Unexpected character: {c!r} at position {i}")

    tokens.append(Token(TOK_EOF, ''))
    return tokens


# ------------------------------------------------------------------ parser

class _Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def consume(self, expected_type: Optional[str] = None) -> Token:
        tok = self.tokens[self.pos]
        if expected_type and tok.type != expected_type:
            raise QueryParseError(
                f"Expected {expected_type}, got {tok.type!r} ({tok.value!r})"
            )
        self.pos += 1
        return tok

    def parse(self) -> dict:
        result = self._parse_or()
        if self.peek().type != TOK_EOF:
            raise QueryParseError(
                f"Unexpected token after expression: {self.peek().value!r}"
            )
        return result

    def _parse_or(self) -> dict:
        left = self._parse_and()
        clauses = [left]
        while self.peek().type == TOK_OR:
            self.consume(TOK_OR)
            clauses.append(self._parse_and())
        if len(clauses) == 1:
            return clauses[0]
        return {'bool': {'should': clauses, 'minimum_should_match': 1}}

    def _parse_and(self) -> dict:
        left = self._parse_not()
        clauses = [left]
        while self.peek().type == TOK_AND:
            self.consume(TOK_AND)
            clauses.append(self._parse_not())
        if len(clauses) == 1:
            return clauses[0]
        return {'bool': {'must': clauses}}

    def _parse_not(self) -> dict:
        if self.peek().type == TOK_NOT:
            self.consume(TOK_NOT)
            operand = self._parse_not()
            return {'bool': {'must_not': [operand]}}
        return self._parse_atom()

    def _parse_atom(self) -> dict:
        if self.peek().type == TOK_LPAREN:
            self.consume(TOK_LPAREN)
            result = self._parse_or()
            self.consume(TOK_RPAREN)
            return result
        return self._parse_condition()

    def _parse_condition(self) -> dict:
        field_tok = self.consume(TOK_WORD)
        field_name = field_tok.value.lower()

        if field_name not in _FIELD_MAP:
            allowed = ', '.join(sorted(_FIELD_MAP.keys()))
            raise QueryParseError(
                f"Unknown field {field_tok.value!r}. Allowed fields: {allowed}"
            )
        es_field = _FIELD_MAP[field_name]

        op_tok = self.peek()

        if op_tok.type == TOK_EQ:
            self.consume(TOK_EQ)
            val_tok = self.consume()
            if val_tok.type not in (TOK_WORD, TOK_STRING):
                raise QueryParseError(
                    f"Expected a value after '=', got {val_tok.type!r}"
                )
            value = val_tok.value
            if field_name == 'level':
                value = value.upper()
            return {'term': {es_field: value}}

        elif op_tok.type == TOK_CONTAINS:
            self.consume(TOK_CONTAINS)
            val_tok = self.consume()
            if val_tok.type not in (TOK_WORD, TOK_STRING):
                raise QueryParseError(
                    f"Expected a value after 'CONTAINS', got {val_tok.type!r}"
                )
            return {'match': {es_field: val_tok.value}}

        else:
            raise QueryParseError(
                f"Expected '=' or 'CONTAINS' after field {field_tok.value!r}, "
                f"got {op_tok.value!r}"
            )


# ------------------------------------------------------------------ public API

def parse_query(query_string: str) -> dict:
    """
    Parse a logical query string and return an Elasticsearch DSL dict.

    Args:
        query_string: The raw query text, e.g.
            '(level = warning OR level = error) AND content CONTAINS "failed"'

    Returns:
        An Elasticsearch query dict suitable for use in the 'query' key of a
        search request body.

    Raises:
        QueryParseError: If the query string is empty or contains syntax errors.
    """
    query_string = query_string.strip()
    if not query_string:
        raise QueryParseError("Query string must not be empty")
    tokens = tokenize(query_string)
    return _Parser(tokens).parse()
