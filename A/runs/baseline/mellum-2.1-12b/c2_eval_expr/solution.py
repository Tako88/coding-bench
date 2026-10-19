import math

def evaluate(expr):
    s = expr
    n = len(s)
    pos = 0

    def skip_spaces():
        nonlocal pos
        while pos < n and s[pos] == ' ':
            pos += 1

    def peek():
        skip_spaces()
        if pos < n:
            return s[pos]
        return None

    def consume():
        nonlocal pos
        skip_spaces()
        if pos < n:
            ch = s[pos]
            pos += 1
            return ch
        return None

    def expect(ch):
        c = consume()
        if c != ch:
            raise ValueError(f"Expected '{ch}' got '{c}'")
        return ch

    def parse_number():
        nonlocal pos
        skip_spaces()
        if pos >= n or not s[pos].isdigit():
            raise ValueError("Number expected")
        start = pos
        # integer part
        while pos < n and s[pos].isdigit():
            pos += 1
        # optional fractional part
        if pos < n and s[pos] == '.':
            pos += 1
            if pos >= n or not s[pos].isdigit():
                raise ValueError("Invalid number: missing digits after decimal")
            while pos < n and s[pos].isdigit():
                pos += 1
        num_str = s[start:pos]
        try:
            return float(num_str)
        except ValueError:
            raise ValueError("Invalid number")

    def parse_primary():
        c = peek()
        if c == '':
            raise ValueError("Unexpected end of expression")
        if c == '(':
            expect('(')
            val = parse_expr()
            expect(')')
            return val
        elif c == '-' or c == '+':
            # primary cannot start with unary operator
            raise ValueError("Unexpected unary operator in primary")
        else:
            # must be a number
            return parse_number()

    def parse_power():
        left = parse_primary()
        if peek() == '^':
            consume()  # '^'
            right = parse_unary()
            if left < 0 and not right.is_integer():
                raise ValueError("Negative base with fractional exponent")
            left = left ** right
            if math.isinf(left):
                raise OverflowError("Result too large")
        return left

    def parse_unary():
        sign = 1.0
        while True:
            c = peek()
            if c == '+':
                consume()
            elif c == '-':
                consume()
                sign = -sign
            else:
                break
        val = parse_power()
        return sign * val

    def parse_term():
        left = parse_unary()
        while True:
            c = peek()
            if c == '*':
                consume()
                right = parse_unary()
                left = left * right
            elif c == '/':
                consume()
                right = parse_unary()
                left = left / right
            else:
                break
        return left

    def parse_expr():
        left = parse_term()
        while True:
            c = peek()
            if c == '+':
                consume()
                right = parse_term()
                left = left + right
            elif c == '-':
                consume()
                right = parse_term()
                left = left - right
            else:
                break
        return left

    result = parse_expr()
    skip_spaces()
    if pos != n:
        raise ValueError(f"Unexpected character '{s[pos]}'")
    return result
