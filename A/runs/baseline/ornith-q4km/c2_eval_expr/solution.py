"""Arithmetic expression evaluator.

Grammar:
  expr    := term (('+' | '-') term)*
  term    := unary (('*' | '/') unary)*
  unary   := ('+' | '-')* power
  power   := primary ('^' unary)?          # '^' is right associative
  primary := number | '(' expr ')'
  number  := digit+ ('.' digit+)?
"""


class _Parser:
    def __init__(self, s):
        self.s = s
        self.pos = 0
        self.n = len(s)

    def error(self):
        raise ValueError("invalid expression: {!r}".format(self.s))

    def skip_spaces(self):
        while self.pos < self.n and self.s[self.pos] == ' ':
            self.pos += 1

    def peek(self):
        self.skip_spaces()
        if self.pos < self.n:
            return self.s[self.pos]
        return None

    def parse_expr(self):
        value = self.parse_term()
        while True:
            c = self.peek()
            if c == '+':
                self.pos += 1
                rhs = self.parse_term()
                value = value + rhs
            elif c == '-':
                self.pos += 1
                rhs = self.parse_term()
                value = value - rhs
            else:
                break
        return value

    def parse_term(self):
        value = self.parse_unary()
        while True:
            c = self.peek()
            if c == '*':
                self.pos += 1
                rhs = self.parse_unary()
                value = value * rhs
            elif c == '/':
                self.pos += 1
                rhs = self.parse_unary()
                value = value / rhs
            else:
                break
        return value

    def parse_unary(self):
        neg = 0
        while True:
            c = self.peek()
            if c == '+':
                self.pos += 1
            elif c == '-':
                self.pos += 1
                neg += 1
            else:
                break
        value = self.parse_power()
        if neg & 1:
            value = -value
        return value

    def parse_power(self):
        base = self.parse_primary()
        if self.peek() == '^':
            self.pos += 1
            exp = self.parse_unary()
            if base < 0 and not float(exp).is_integer():
                raise ValueError(
                    "negative base to a non-integer exponent is undefined")
            return base ** exp
        return base

    def parse_primary(self):
        c = self.peek()
        if c == '(':
            self.pos += 1
            value = self.parse_expr()
            self.skip_spaces()
            if self.pos >= self.n or self.s[self.pos] != ')':
                self.error()
            self.pos += 1
            return value
        if c is not None and c.isdigit():
            return self.parse_number()
        self.error()

    def parse_number(self):
        start = self.pos
        while self.pos < self.n and self.s[self.pos].isdigit():
            self.pos += 1
        int_end = self.pos
        result = None
        if self.pos < self.n and self.s[self.pos] == '.':
            self.pos += 1
            frac_start = self.pos
            while self.pos < self.n and self.s[self.pos].isdigit():
                self.pos += 1
            if self.pos == frac_start:
                self.error()
            result = float(self.s[start:self.pos])
        if result is None:
            if self.pos == start:
                self.error()
            result = int(self.s[start:int_end])
        return result


def evaluate(expr):
    if not isinstance(expr, str):
        raise ValueError("expression must be a string")
    p = _Parser(expr)
    value = p.parse_expr()
    p.skip_spaces()
    if p.pos != p.n:
        p.error()
    return float(value)
