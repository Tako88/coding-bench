"""Arithmetic expression evaluator.

Implements ``evaluate(expr)`` for the following grammar (the only whitespace
character allowed is the single space ' ', which may appear between tokens):

    expr    := term (('+' | '-') term)*
    term    := unary (('*' | '/') unary)*
    unary   := ('+' | '-')* power
    power   := primary ('^' unary)?          # '^' is right associative
    primary := number | '(' expr ')'
    number  := digit+ ('.' digit+)?          # digits on both sides of '.'

All arithmetic is done in double precision and the result is always a
``float``.  ``ValueError`` is raised for any input that is not derivable
from the grammar.  ``ZeroDivisionError`` and ``OverflowError`` arising from
the arithmetic itself propagate unchanged, and a negative base raised to a
fractional exponent raises ``ValueError``.
"""

_DIGITS = frozenset("0123456789")
_OPERATORS = frozenset("+-*/^")
# Relative precedence: expr < term < unary sign < power.
_PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, "u+": 3, "u-": 3, "^": 4}
_INF = float("inf")


def evaluate(expr):
    """Evaluate the arithmetic expression *expr* and return it as a float.

    Raises ``ValueError`` for any input that is not derivable from the
    grammar.  ``ZeroDivisionError`` and ``OverflowError`` raised by the
    arithmetic itself (e.g. ``1/0`` or ``2^5^5``) propagate out of this
    function.
    """
    if not isinstance(expr, str):
        raise ValueError("expression must be a string")
    tokens = _tokenize(expr)
    _validate(tokens)
    return _evaluate_tokens(tokens)


def _tokenize(text):
    """Split *text* into ("num", float) / ("op", str) tokens.

    Raises ValueError for illegal characters and for decimal literals that
    do not have digits on both sides of the dot.
    """
    tokens = []
    n = len(text)
    i = 0
    while i < n:
        c = text[i]
        if c == " ":
            i += 1
        elif c in _DIGITS:
            start = i
            while i < n and text[i] in _DIGITS:
                i += 1
            if i < n and text[i] == ".":
                i += 1
                if i >= n or text[i] not in _DIGITS:
                    raise ValueError(
                        "a number needs digits on both sides of '.'")
                while i < n and text[i] in _DIGITS:
                    i += 1
            value = float(text[start:i])
            if value == _INF:
                raise OverflowError(
                    "number is too large to be represented as a float")
            tokens.append(("num", value))
        elif c in _OPERATORS or c in "()":
            tokens.append(("op", c))
            i += 1
        else:
            raise ValueError("invalid character %r" % c)
    return tokens


def _validate(tokens):
    """Raise ValueError unless *tokens* are derivable from the grammar.

    This purely syntactic pass must finish before any arithmetic is done so
    that a malformed expression always yields ValueError even if a
    sub-expression of it (like ``1/0``) would raise a runtime error.
    """
    expect_operand = True
    depth = 0
    for kind, tok in tokens:
        if kind == "num":
            if not expect_operand:
                raise ValueError("two operands are adjacent")
            expect_operand = False
        elif tok == "(":
            if not expect_operand:
                raise ValueError("missing operator before '('")
            depth += 1
            expect_operand = True
        elif tok == ")":
            if expect_operand:
                raise ValueError("empty or misplaced parentheses")
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced ')'")
            expect_operand = False
        else:  # a binary operator: '+' '-' '*' '/' '^'
            if tok in "*/^" and expect_operand:
                raise ValueError("missing operand before %r" % tok)
            # A '+' or '-' is unary where an operand is expected and binary
            # otherwise; either reading is grammatical, so no error here.
            expect_operand = True
    if expect_operand:
        raise ValueError("missing operand at end of expression")
    if depth:
        raise ValueError("unbalanced '('")


def _evaluate_tokens(tokens):
    """Evaluate a validated token stream with the shunting-yard algorithm."""
    values = []
    ops = []
    expect_operand = True
    for kind, tok in tokens:
        if kind == "num":
            values.append(tok)
            expect_operand = False
        elif tok == "(":
            ops.append(tok)
            expect_operand = True
        elif tok == ")":
            while ops[-1] != "(":
                _apply(ops.pop(), values)
            ops.pop()
            expect_operand = False
        elif tok in "+-":
            if expect_operand:
                # unary sign: it applies to the power that follows, so it is
                # simply pushed (nothing pops, since it binds tighter than
                # any binary operator except '^', and '^' follows it).
                ops.append("u" + tok)
            else:
                # binary '+'/'-' are left associative and have the lowest
                # precedence, so everything on the stack applies first.
                while ops and ops[-1] != "(":
                    _apply(ops.pop(), values)
                ops.append(tok)
            expect_operand = True
        else:  # '*' '/' '^'
            if tok != "^":
                # left associative; apply anything of precedence >= 2
                # ('*', '/', unary signs and '^' all bind tighter or equal).
                while ops and ops[-1] != "(" \
                        and _PRECEDENCE[ops[-1]] >= 2:
                    _apply(ops.pop(), values)
            # '^' is right associative with the highest precedence: it never
            # pops anything when read.
            ops.append(tok)
            expect_operand = True
    while ops:
        _apply(ops.pop(), values)
    return values[0]


def _apply(op, values):
    """Pop the operands of *op* from *values* and push the result."""
    if op == "u-":
        values.append(-values.pop())
    elif op == "u+":
        values.append(values.pop())
    else:
        right = values.pop()
        left = values.pop()
        if op == "+":
            values.append(left + right)
        elif op == "-":
            values.append(left - right)
        elif op == "*":
            values.append(left * right)
        elif op == "/":
            values.append(left / right)
        else:  # "^"
            values.append(_pow(left, right))


def _pow(base, exponent):
    """``base ** exponent`` with the real-valued power rules of the spec."""
    if base < 0.0 and not exponent.is_integer():
        raise ValueError(
            "negative number cannot be raised to a fractional power")
    return base ** exponent
