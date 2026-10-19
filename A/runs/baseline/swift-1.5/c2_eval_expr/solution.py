"""Arithmetic expression evaluator.

Grammar (complete; anything not derivable from it is a ValueError):

    expr    := term (('+' | '-') term)*
    term    := unary (('*' | '/') unary)*
    unary   := ('+' | '-')* power
    power   := primary ('^' unary)?          # '^' is right associative
    primary := number | '(' expr ')'
    number  := digit+ ('.' digit+)?

The result is always a float.  Division by zero propagates
ZeroDivisionError, values too large for a float propagate OverflowError,
and a negative base raised to a fractional power raises ValueError.
"""

_DIGITS = frozenset('0123456789')


class _Parser:
    """Recursive-descent parser for the grammar above."""

    def __init__(self, text):
        self.text = text
        self.pos = 0

    # -- low-level helpers -------------------------------------------------

    def _peek(self):
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def _skip_spaces(self):
        while self.pos < len(self.text) and self.text[self.pos] == ' ':
            self.pos += 1

    # -- grammar rules -----------------------------------------------------

    def parse_expr(self):
        value = self.parse_term()
        while True:
            self._skip_spaces()
            c = self._peek()
            if c == '+' or c == '-':
                self.pos += 1
                rhs = self.parse_term()
                value = value + rhs if c == '+' else value - rhs
            else:
                return value

    def parse_term(self):
        value = self.parse_unary()
        while True:
            self._skip_spaces()
            c = self._peek()
            if c == '*' or c == '/':
                self.pos += 1
                rhs = self.parse_unary()
                value = value * rhs if c == '*' else value / rhs
            else:
                return value

    def parse_unary(self):
        sign = 1
        while True:
            self._skip_spaces()
            c = self._peek()
            if c == '+':
                self.pos += 1
            elif c == '-':
                self.pos += 1
                sign = -sign
            else:
                break
        return sign * self.parse_power()

    def parse_power(self):
        base = self.parse_primary()
        self._skip_spaces()
        if self._peek() == '^':
            self.pos += 1
            exponent = self.parse_unary()
            return _pow(base, exponent)
        return base

    def parse_primary(self):
        self._skip_spaces()
        c = self._peek()
        if c is None:
            raise ValueError('unexpected end of expression')
        if c == '(':
            self.pos += 1
            value = self.parse_expr()
            self._skip_spaces()
            if self._peek() != ')':
                raise ValueError("expected ')'")
            self.pos += 1
            return value
        if c in _DIGITS:
            return self.parse_number()
        raise ValueError('unexpected character %r' % c)

    def parse_number(self):
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] in _DIGITS:
            self.pos += 1
        if self.pos < len(self.text) and self.text[self.pos] == '.':
            nxt = self.pos + 1
            if nxt >= len(self.text) or self.text[nxt] not in _DIGITS:
                raise ValueError("number requires digits after '.'")
            self.pos = nxt
            while self.pos < len(self.text) and self.text[self.pos] in _DIGITS:
                self.pos += 1
        return float(self.text[start:self.pos])


def _pow(base, exponent):
    """Floating power with the extra real-valuedness check."""
    if base < 0 and exponent != int(exponent):
        raise ValueError('negative base to a fractional power')
    return base ** exponent


def evaluate(expr):
    """Evaluate the arithmetic expression *expr* and return the result as a float.

    Raises:
        ValueError: for any input not derivable from the grammar.
        ZeroDivisionError: for division by zero (propagated, not caught).
        OverflowError: for results too large to be represented as a float.
    """
    parser = _Parser(expr)
    parser._skip_spaces()
    if parser.pos >= len(parser.text):
        raise ValueError('empty expression')
    value = parser.parse_expr()
    parser._skip_spaces()
    if parser.pos < len(parser.text):
        raise ValueError('trailing characters in expression')
    return float(value)
