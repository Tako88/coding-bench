"""Arithmetic expression evaluator.

Grammar:
  expr    := term (('+' | '-') term)*
  term    := unary (('*' | '/') unary)*
  unary   := ('+' | '-')* power
  power   := primary ('^' unary)?          # '^' is right associative
  primary := number | '(' expr ')'
  number  := digit+ ('.' digit+)?

Everything is evaluated in float. Division by zero raises ZeroDivisionError
(propagates). Overflow raises OverflowError. A negative base raised to a
non-integer exponent raises ValueError.
"""


def _tokenize(s):
    tokens = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == ' ':
            i += 1
            continue
        if c in '+-*/^()':
            tokens.append(c)
            i += 1
            continue
        if c.isdigit() or c == '.':
            start = i
            digits_before = 0
            while i < n and s[i].isdigit():
                i += 1
                digits_before += 1
            if i < n and s[i] == '.':
                i += 1
                digits_after = 0
                while i < n and s[i].isdigit():
                    i += 1
                    digits_after += 1
                if digits_after == 0:
                    raise ValueError("digits required after the decimal point")
            if digits_before == 0:
                raise ValueError("digits required before the decimal point")
            tokens.append(s[start:i])
            continue
        raise ValueError("invalid character: %r" % c)
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def advance(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def parse_expr(self):
        val = self.parse_term()
        while self.peek() in ('+', '-'):
            op = self.advance()
            rhs = self.parse_term()
            val = val + rhs if op == '+' else val - rhs
        return val

    def parse_term(self):
        val = self.parse_unary()
        while self.peek() in ('*', '/'):
            op = self.advance()
            rhs = self.parse_unary()
            val = val * rhs if op == '*' else val / rhs
        return val

    def parse_unary(self):
        if self.peek() in ('+', '-'):
            op = self.advance()
            val = self.parse_unary()
            return -val if op == '-' else val
        return self.parse_power()

    def parse_power(self):
        base = self.parse_primary()
        if self.peek() == '^':
            self.advance()
            exp = self.parse_unary()
            result = base ** exp
            if base < 0 and not exp.is_integer():
                raise ValueError(
                    "negative base %r raised to non-integer exponent %r"
                    % (base, exp))
            return result
        return base

    def parse_primary(self):
        t = self.peek()
        if t == '(':
            self.advance()
            val = self.parse_expr()
            if self.peek() != ')':
                raise ValueError("expected ')'")
            self.advance()
            return val
        if t is None or t in ('+', '-', '*', '/', ')'):
            raise ValueError("unexpected token: %r" % (t,))
        return float(self.advance())


def evaluate(expr):
    if not isinstance(expr, str):
        raise ValueError("input must be a string")
    tokens = _tokenize(expr)
    if not tokens:
        raise ValueError("empty expression")
    parser = _Parser(tokens)
    result = parser.parse_expr()
    if parser.i != len(parser.toks):
        raise ValueError("trailing tokens")
    return float(result)
