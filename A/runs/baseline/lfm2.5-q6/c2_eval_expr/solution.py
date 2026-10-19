import math


def evaluate(expr):
    # Empty or whitespace-only expressions are errors
    if not expr or all(c == ' ' for c in expr):
        raise ValueError("Empty expression")

    # Validate characters - only digits, ., +-*/^(), and spaces allowed
    allowed = set('0123456789.+-*/^() ')
    for ch in expr:
        if ch not in allowed:
            raise ValueError(f"Invalid character: {ch}")

    tokens = tokenize(expr)
    parser = Parser(tokens)
    result = parser.parse_expr()

    # Ensure all tokens were consumed
    if parser.pos < len(tokens):
        raise ValueError("Unexpected trailing input")

    return float(result)


def tokenize(expr):
    """Convert expression string into a list of tokens."""
    tokens = []
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch == ' ':
            # Skip spaces
            i += 1
            continue
        elif ch.isdigit():
            start = i
            # Collect integer part
            while i < n and expr[i].isdigit():
                i += 1
            # Check for decimal point and fractional part
            if i < n and expr[i] == '.':
                i += 1
                # Fractional part must have at least one digit
                if i >= n or not expr[i].isdigit():
                    raise ValueError("Invalid number format")
                while i < n and expr[i].isdigit():
                    i += 1
            tokens.append(('NUMBER', expr[start:i]))
        elif ch in '+-*/^()':
            tokens.append((ch, ch))
            i += 1
        else:
            # Should not happen due to character validation
            raise ValueError(f"Invalid character: {ch}")
    return tokens


class Parser:
    """Recursive descent parser for arithmetic expressions."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self):
        token = self.peek()
        if token is None:
            raise ValueError("Unexpected end of input")
        self.pos += 1
        return token

    def parse_expr(self):
        # expr := term (('+' | '-') term)*
        result = self.parse_term()
        while self.peek() and self.peek()[0] in ('+', '-'):
            op_token = self.consume()
            right = self.parse_term()
            if op_token[1] == '+':
                result += right
            else:
                result -= right
        return result

    def parse_term(self):
        # term := unary (('*' | '/') unary)*
        result = self.parse_unary()
        while self.peek() and self.peek()[0] in ('*', '/'):
            op_token = self.consume()
            right = self.parse_unary()
            if op_token[1] == '*':
                result *= right
            else:
                if right == 0:
                    raise ZeroDivisionError("division by zero")
                result /= right
        return result

    def parse_unary(self):
        # unary := ('+' | '-')* power
        sign = 1
        if self.peek() is None:
            raise ValueError("Unexpected end of input")
        while self.peek() and self.peek()[0] in ('+', '-'):
            if self.peek()[1] == '-':
                sign *= -1
            self.consume()
        return sign * self.parse_power()

    def parse_power(self):
        # power := primary ('^' unary)?
        result = self.parse_primary()
        if self.peek() and self.peek()[0] == '^':
            self.consume()
            exponent = self.parse_unary()
            result = result ** exponent
            # Negative base with fractional exponent has no real value
            if isinstance(result, complex) and result.imag != 0:
                raise ValueError("Negative base with fractional exponent")
        return result

    def parse_primary(self):
        # primary := number | '(' expr ')'
        token = self.peek()
        if token is None:
            raise ValueError("Unexpected end of input")
        if token[0] == 'NUMBER':
            self.consume()
            return float(token[1])
        elif token[0] == '(':
            self.consume()
            result = self.parse_expr()
            if self.peek() is None or self.peek()[0] != ')':
                raise ValueError("Expected ')'")
            self.consume()
            return result
        else:
            raise ValueError("Unexpected token")
