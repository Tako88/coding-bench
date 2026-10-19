"""Arithmetic expression evaluator following the specified grammar."""


def evaluate(expr: str) -> float:
    """Evaluate an arithmetic expression string and return the result as a float."""

    class Token:
        NUMBER = 'NUMBER'
        PLUS = 'PLUS'
        MINUS = 'MINUS'
        MUL = 'MUL'
        DIV = 'DIV'
        POW = 'POW'
        LPAREN = 'LPAREN'
        RPAREN = 'RPAREN'
        EOF = 'EOF'

    # Valid characters
    for ch in expr:
        if ch not in '0123456789.+-*/^() ':
            raise ValueError(f"Invalid character: {ch!r}")

    if not expr or expr.strip() == '':
        raise ValueError("Empty or whitespace-only expression")

    class Lexer:
        def __init__(self, text):
            self.text = text
            self.pos = 0

        def peek(self):
            if self.pos < len(self.text):
                return self.text[self.pos]
            return None

        def advance(self):
            ch = self.text[self.pos]
            self.pos += 1
            return ch

        def at_end(self):
            return self.pos >= len(self.text)

        def skip_spaces(self):
            while not self.at_end() and self.text[self.pos] == ' ':
                self.pos += 1

        def parse_number(self):
            start = self.pos
            while not self.at_end() and self.text[self.pos].isdigit():
                self.pos += 1
            if self.pos == start:
                raise ValueError("Expected digit")
            has_dot = False
            if not self.at_end() and self.text[self.pos] == '.':
                has_dot = True
                self.pos += 1
                if self.at_end() or not self.text[self.pos].isdigit():
                    raise ValueError("Expected digit after decimal point")
                while not self.at_end() and self.text[self.pos].isdigit():
                    self.pos += 1
            return float(self.text[start:self.pos])

        def tokenize(self):
            tokens = []
            while not self.at_end():
                self.skip_spaces()
                if self.at_end():
                    break
                ch = self.peek()
                if ch.isdigit():
                    tokens.append((Token.NUMBER, self.parse_number()))
                elif ch == '+':
                    tokens.append((Token.PLUS, '+'))
                    self.advance()
                elif ch == '-':
                    tokens.append((Token.MINUS, '-'))
                    self.advance()
                elif ch == '*':
                    tokens.append((Token.MUL, '*'))
                    self.advance()
                elif ch == '/':
                    tokens.append((Token.DIV, '/'))
                    self.advance()
                elif ch == '^':
                    tokens.append((Token.POW, '^'))
                    self.advance()
                elif ch == '(':
                    tokens.append((Token.LPAREN, '('))
                    self.advance()
                elif ch == ')':
                    tokens.append((Token.RPAREN, ')'))
                    self.advance()
                elif ch == ' ':
                    self.advance()
                else:
                    raise ValueError(f"Invalid character: {ch!r}")
            tokens.append((Token.EOF, None))
            return tokens

    class Parser:
        def __init__(self, tokens):
            self.tokens = tokens
            self.pos = 0

        def peek(self):
            if self.pos < len(self.tokens):
                return self.tokens[self.pos]
            return (Token.EOF, None)

        def advance(self):
            tok = self.tokens[self.pos]
            self.pos += 1
            return tok

        def expect(self, tok_type):
            tok = self.peek()
            if tok[0] != tok_type:
                raise ValueError(f"Expected {tok_type}, got {tok}")
            return self.advance()

        def parse_expr(self):
            """expr := term (('+' | '-') term)*"""
            left = self.parse_term()
            while self.peek()[0] in (Token.PLUS, Token.MINUS):
                op = self.advance()[0]
                right = self.parse_term()
                if op == Token.PLUS:
                    left = left + right
                else:
                    left = left - right
            return left

        def parse_term(self):
            """term := unary (('*' | '/') unary)*"""
            left = self.parse_unary()
            while self.peek()[0] in (Token.MUL, Token.DIV):
                op = self.advance()[0]
                right = self.parse_unary()
                if op == Token.MUL:
                    left = left * right
                else:
                    left = left / right
            return left

        def parse_unary(self):
            """unary := ('+' | '-')* power"""
            sign = 1
            while self.peek()[0] in (Token.PLUS, Token.MINUS):
                op = self.advance()[0]
                if op == Token.MINUS:
                    sign = -sign
            val = self.parse_power()
            return sign * val

        def parse_power(self):
            """power := primary ('^' unary)?"""
            base = self.parse_primary()
            if self.peek()[0] == Token.POW:
                self.advance()
                exp = self.parse_unary()
                base = self._pow(base, exp)
            return base

        def _pow(self, base, exp):
            """Compute base**exp, raising ValueError for complex results."""
            try:
                result = base ** exp
            except OverflowError:
                raise
            if isinstance(result, complex):
                raise ValueError("Negative base with fractional exponent")
            return float(result)

        def parse_primary(self):
            """primary := number | '(' expr ')'"""
            tok = self.peek()
            if tok[0] == Token.NUMBER:
                self.advance()
                return tok[1]
            elif tok[0] == Token.LPAREN:
                self.advance()
                val = self.parse_expr()
                self.expect(Token.RPAREN)
                return val
            else:
                raise ValueError(f"Unexpected token: {tok}")

    lexer = Lexer(expr)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    result = parser.parse_expr()

    # Check that we consumed all tokens
    if parser.peek()[0] != Token.EOF:
        raise ValueError("Unexpected tokens remaining")

    return float(result)
