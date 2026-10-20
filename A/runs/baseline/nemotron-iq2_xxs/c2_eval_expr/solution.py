def evaluate(expr):
    """Evaluate an arithmetic expression and return a float.

    Grammar:
        expr    := term (('+' | '-') term)*
        term    := unary (('*' | '/') unary)*
        unary   := ('+' | '-')* power
        power   := primary ('^' unary)?
        primary := number | '(' expr ')'
        number  := digit+ ('.' digit+)?
    """
    if not isinstance(expr, str):
        raise ValueError("expression must be a string")
    allowed = set("0123456789.+-*/^() ")
    for ch in expr:
        if ch not in allowed:
            raise ValueError("invalid character %r" % ch)
    return Parser(expr).parse()


class Parser:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def parse(self):
        value = self.expr()
        if self.i != len(self.s):
            raise ValueError("unexpected characters at end of expression")
        return value

    def _skip(self):
        while self.i < len(self.s) and self.s[self.i] == ' ':
            self.i += 1

    def _peek(self):
        self._skip()
        if self.i >= len(self.s):
            return None
        return self.s[self.i]

    def expr(self):
        left = self.term()
        while True:
            self._skip()
            if self.i < len(self.s) and self.s[self.i] in '+-':
                op = self.s[self.i]
                self.i += 1
                right = self.term()
                left = left + right if op == '+' else left - right
            else:
                break
        return left

    def term(self):
        left = self.unary()
        while True:
            self._skip()
            if self.i < len(self.s) and self.s[self.i] in '*/':
                op = self.s[self.i]
                self.i += 1
                right = self.unary()
                left = left * right if op == '*' else left / right
            else:
                break
        return left

    def unary(self):
        sign = 1.0
        while True:
            self._skip()
            if self.i < len(self.s) and self.s[self.i] in '+-':
                if self.s[self.i] == '-':
                    sign = -sign
                self.i += 1
            else:
                break
        return sign * self.power()

    def power(self):
        base = self.primary()
        self._skip()
        if self.i < len(self.s) and self.s[self.i] == '^':
            self.i += 1
            exp = self.unary()
            if base < 0 and not exp.is_integer():
                raise ValueError("negative base raised to a fractional exponent")
            return base ** exp
        return base

    def primary(self):
        self._skip()
        if self.i >= len(self.s):
            raise ValueError("unexpected end of expression")
        ch = self.s[self.i]
        if ch == '(':
            self.i += 1
            value = self.expr()
            self._skip()
            if self.i >= len(self.s) or self.s[self.i] != ')':
                raise ValueError("missing closing parenthesis")
            self.i += 1
            return value
        if ch == '.' or not ('0' <= ch <= '9'):
            raise ValueError("expected number or '('")
        return self.number()

    def number(self):
        start = self.i
        while self.i < len(self.s) and '0' <= self.s[self.i] <= '9':
            self.i += 1
        if self.i == start:
            raise ValueError("expected digits")
        if self.i < len(self.s) and self.s[self.i] == '.':
            self.i += 1
            if self.i >= len(self.s) or not ('0' <= self.s[self.i] <= '9'):
                raise ValueError("expected digits after decimal point")
            while self.i < len(self.s) and '0' <= self.s[self.i] <= '9':
                self.i += 1
        return float(self.s[start:self.i])
