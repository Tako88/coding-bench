"""Arithmetic expression evaluator (see TASK.md)."""

import re

_TOKEN_RE = re.compile(r"\d+(?:\.\d+)?|[+\-*/^()]")
_NUMBER_RE = re.compile(r"\d+(\.\d+)?")


def _tokenize(expr):
    tokens = []
    i = 0
    n = len(expr)
    while i < n:
        c = expr[i]
        if c == " ":
            i += 1
            continue
        m = _TOKEN_RE.match(expr, i)
        if m is None:
            raise ValueError("invalid character: %r" % c)
        tokens.append(m.group())
        i = m.end()
    return tokens


def _pow(base, exp):
    if base < 0 and not float(exp).is_integer():
        raise ValueError("negative base with fractional exponent")
    return base ** exp


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def parse(self):
        value = self.expr()
        if self.pos != len(self.tokens):
            raise ValueError("unexpected trailing tokens")
        return value

    def expr(self):
        value = self.term()
        while self.peek() in ("+", "-"):
            op = self.advance()
            rhs = self.term()
            value = value + rhs if op == "+" else value - rhs
        return value

    def term(self):
        value = self.unary()
        while self.peek() in ("*", "/"):
            op = self.advance()
            rhs = self.unary()
            value = value * rhs if op == "*" else value / rhs
        return value

    def unary(self):
        sign = 1.0
        while self.peek() in ("+", "-"):
            if self.advance() == "-":
                sign = -sign
        value = self.power()
        return value * sign

    def power(self):
        base = self.primary()
        if self.peek() == "^":
            self.advance()
            exp = self.unary()
            return _pow(base, exp)
        return base

    def primary(self):
        tok = self.peek()
        if tok is None:
            raise ValueError("unexpected end of expression")
        if tok == "(":
            self.advance()
            value = self.expr()
            if self.peek() != ")":
                raise ValueError("expected closing parenthesis")
            self.advance()
            return value
        if _NUMBER_RE.fullmatch(tok):
            self.advance()
            return float(tok)
        raise ValueError("unexpected token: %r" % (tok,))


def evaluate(expr):
    if not isinstance(expr, str):
        raise ValueError("expression must be a string")
    tokens = _tokenize(expr)
    parser = _Parser(tokens)
    result = parser.parse()
    return float(result)
