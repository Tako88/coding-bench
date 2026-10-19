"""Arithmetic expression evaluator (see TASK.md).

Grammar (complete; anything not derivable from it is a ValueError):

  expr    := term (('+' | '-') term)*
  term    := unary (('*' | '/') unary)*
  unary   := ('+' | '-')* power
  power   := primary ('^' unary)?          # '^' is right associative
  primary := number | '(' expr ')'
  number  := digit+ ('.' digit+)?          # digits required on both sides of '.'

Semantics:
- integer literals parse to int, decimal literals to float; operators use
  Python's native arithmetic, so e.g. 1/0 raises ZeroDivisionError,
  (-8)**0.5 raises ValueError and int**int stays exact until the final
  conversion, making 2^5^5 raise OverflowError when converted to float;
- '^' binds tighter than * and /, is right associative, and unary signs bind
  looser than '^', so -2^2 is -4 and 2^3^2 is 512;
- only the space character ' ' is allowed as whitespace.
"""

from math import log2

__all__ = ["evaluate"]

_DIGITS = frozenset("0123456789")

# A float can represent integers up to ~2**1024.  If an exact integer result
# is already far larger than that (and hence certain to overflow), raising
# OverflowError early is safe: it is the same exception the final float()
# conversion would raise, and it avoids allocating an enormous integer.
_BIT_GUARD = 1_000_000


def _pow(base, expo):
    """Evaluate ``base ** expo`` (base/expo are int or float).

    Raises the natural ZeroDivisionError / ValueError / OverflowError.
    """
    if isinstance(base, int) and isinstance(expo, int) and expo > 0:
        b = abs(base)
        if b >= 2 and expo * log2(b) > _BIT_GUARD:
            raise OverflowError("result too large to represent as a float")
    return base ** expo


class _Parser:
    """Recursive-descent parser/evaluator for the grammar above."""

    def __init__(self, s):
        self.s = s
        self.i = 0
        self.n = len(s)

    def _skip(self):
        while self.i < self.n and self.s[self.i] == " ":
            self.i += 1

    def _peek(self):
        return self.s[self.i] if self.i < self.n else ""

    def _expr(self):
        v = self._term()
        while True:
            self._skip()
            c = self._peek()
            if c == "+":
                self.i += 1
                r = self._term()
                v = v + r
            elif c == "-":
                self.i += 1
                r = self._term()
                v = v - r
            else:
                break
        return v

    def _term(self):
        v = self._unary()
        while True:
            self._skip()
            c = self._peek()
            if c == "*":
                self.i += 1
                r = self._unary()
                v = v * r
            elif c == "/":
                self.i += 1
                r = self._unary()
                v = v / r
            else:
                break
        return v

    def _unary(self):
        neg = False
        while True:
            self._skip()
            c = self._peek()
            if c == "+":
                self.i += 1
            elif c == "-":
                self.i += 1
                neg = not neg
            else:
                break
        v = self._power()
        return -v if neg else v

    def _power(self):
        base = self._primary()
        self._skip()
        if self._peek() == "^":
            self.i += 1
            expo = self._unary()
            return _pow(base, expo)
        return base

    def _primary(self):
        self._skip()
        c = self._peek()
        if c == "(":
            self.i += 1
            v = self._expr()
            self._skip()
            if self.i >= self.n or self.s[self.i] != ")":
                raise ValueError("closing parenthesis expected")
            self.i += 1
            return v
        if c in _DIGITS:
            return self._number()
        raise ValueError("unexpected character in expression")

    def _number(self):
        start = self.i
        while self.i < self.n and self.s[self.i] in _DIGITS:
            self.i += 1
        if self.i < self.n and self.s[self.i] == ".":
            self.i += 1
            if self.i >= self.n or self.s[self.i] not in _DIGITS:
                raise ValueError("digit expected after the decimal point")
            while self.i < self.n and self.s[self.i] in _DIGITS:
                self.i += 1
            return float(self.s[start:self.i])
        return int(self.s[start:self.i])


def evaluate(expr):
    """Evaluate an arithmetic expression string and return a float.

    Raises:
        ValueError: for any input not derivable from the grammar (including
            negative base with a fractional exponent, e.g. (-8)^0.5).
        ZeroDivisionError: for division by zero.
        OverflowError: when the result cannot be represented as a float.
    """
    if not isinstance(expr, str):
        raise ValueError("expression must be a string")
    p = _Parser(expr)
    v = p._expr()
    p._skip()
    if p.i != p.n:
        raise ValueError("unexpected trailing characters in expression")
    # Final conversion: exact integer results that are too large raise
    # OverflowError here (e.g. 2^5^5 = 2^(5^5)).
    return float(v)
