"""Arithmetic expression evaluator.

Grammar (from TASK.md):

  expr    := term (('+' | '-') term)*
  term    := unary (('*' | '/') unary)*
  unary   := ('+' | '-')* power
  power   := primary ('^' unary)?          # '^' is right associative
  primary := number | '(' expr ')'
  number  := digit+ ('.' digit+)?

Anything not derivable from the grammar raises ValueError.
Division by zero raises ZeroDivisionError; float overflow raises OverflowError;
a negative base raised to a non-integral exponent raises ValueError.
"""

from __future__ import annotations

DIGITS = "0123456789"
OPERATORS = "+-*/^()"
SPACES = " "


def evaluate(expr):
    """Evaluate *expr* (a string) and return the result as a float.

    Raises ValueError for malformed input, ZeroDivisionError for division by
    zero, and OverflowError when a value cannot be represented as a float.
    """
    if not isinstance(expr, str):
        raise ValueError("expression must be a string")

    tokens = _tokenize(expr)
    parser = _Parser(tokens)
    value = parser.parse_expr()
    parser.expect_eof()
    return float(value)


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

def _tokenize(expr):
    """Return a list of (kind, value) tokens, ending with ('EOF', None).

    kind is one of 'NUM', '+', '-', '*', '/', '^', '(', ')', 'EOF'.
    Raises ValueError on any character outside the allowed set and on
    malformed number literals.
    """
    tokens = []
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch == " ":
            i += 1
            continue
        if ch in DIGITS:
            start = i
            while i < n and expr[i] in DIGITS:
                i += 1
            if i < n and expr[i] == ".":
                i += 1
                if i >= n or expr[i] not in DIGITS:
                    raise ValueError("malformed number: digits required after '.'")
                while i < n and expr[i] in DIGITS:
                    i += 1
            text = expr[start:i]
            tokens.append(("NUM", float(text)))
            continue
        if ch in OPERATORS:
            tokens.append((ch, None))
            i += 1
            continue
        # Any other character (letters, tab, newline, '_', ',', etc.) is an error.
        raise ValueError("unexpected character: %r" % (ch,))
    tokens.append(("EOF", None))
    return tokens


# ---------------------------------------------------------------------------
# Recursive-descent parser (also evaluates while parsing)
# ---------------------------------------------------------------------------

class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        return self.tokens[self.pos][0]

    def _consume(self, kind):
        tok = self.tokens[self.pos]
        if tok[0] != kind:
            raise ValueError("expected %r, got %r" % (kind, tok[0]))
        self.pos += 1
        return tok

    def _accept(self, kind):
        if self.tokens[self.pos][0] == kind:
            self.pos += 1
            return True
        return False

    def expect_eof(self):
        if self._peek() != "EOF":
            raise ValueError("trailing input: expression must be complete")

    def parse_expr(self):
        value = self.parse_term()
        while True:
            op = self._peek()
            if op == "+":
                self.pos += 1
                value = value + self.parse_term()
            elif op == "-":
                self.pos += 1
                value = value - self.parse_term()
            else:
                return value

    def parse_term(self):
        value = self.parse_unary()
        while True:
            op = self._peek()
            if op == "*":
                self.pos += 1
                value = value * self.parse_unary()
            elif op == "/":
                self.pos += 1
                value = self._divide(value, self.parse_unary())
            else:
                return value

    def parse_unary(self):
        negate = False
        while True:
            op = self._peek()
            if op == "+":
                self.pos += 1
            elif op == "-":
                self.pos += 1
                negate = not negate
            else:
                break
        value = self.parse_power()
        return -value if negate else value

    def parse_power(self):
        base = self.parse_primary()
        if self._peek() == "^":
            self.pos += 1
            exponent = self.parse_unary()
            base = self._power(base, exponent)
        return base

    def parse_primary(self):
        kind, value = self.tokens[self.pos]
        if kind == "NUM":
            self.pos += 1
            return value
        if kind == "(":
            self.pos += 1
            inner = self.parse_expr()
            # Parentheses must be non-empty and balanced.
            self._consume(")")
            return inner
        raise ValueError("expected a number or '(', got %r" % (kind,))

    # --- arithmetic helpers enforcing the spec's numeric rules ---------------

    def _divide(self, left, right):
        # Let the natural ZeroDivisionError propagate; never a ValueError.
        return left / right

    def _power(self, base, exponent):
        if base < 0.0 and not self._is_integral(exponent):
            # e.g. (-8)^0.5 has no real value -> a syntax/semantic error.
            raise ValueError("negative base raised to a fractional power")
        return base ** exponent

    def _is_integral(self, value):
        try:
            return float(value).is_integer()
        except (ValueError, OverflowError, TypeError):
            return False


if __name__ == "__main__":
    print(evaluate("1+2*3"))
