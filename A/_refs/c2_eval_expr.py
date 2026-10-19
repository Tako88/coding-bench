"""Reference solution for c2_eval_expr. Standalone: a Pratt (binding power)
parser, written differently from the grader's recursive-descent reference."""

# (left binding power, right binding power); equal powers mean right associative
INFIX = {
    "+": (2, 3),
    "-": (2, 3),
    "*": (4, 5),
    "/": (4, 5),
    "^": (6, 6),
}
UNARY_BP = 5  # looser than '^' (6), tighter than '*' and '/' (4)


def _tokens(expr):
    out = []
    i, n = 0, len(expr)
    while i < n:
        c = expr[i]
        if c == " ":
            i += 1
        elif c.isdigit():
            j = i
            while j < n and expr[j].isdigit():
                j += 1
            if j < n and expr[j] == ".":
                k = j + 1
                while k < n and expr[k].isdigit():
                    k += 1
                if k == j + 1:
                    raise ValueError("digit required after dot")
                j = k
            out.append(("n", float(expr[i:j])))
            i = j
        elif c == ".":
            raise ValueError("digit required before dot")
        elif c in "+-*/^()":
            out.append((c, None))
            i += 1
        else:
            raise ValueError("invalid character %r" % (c,))
    return out


def evaluate(expr):
    toks = _tokens(expr)
    pos = [0]

    def peek():
        return toks[pos[0]][0] if pos[0] < len(toks) else None

    def take():
        if pos[0] >= len(toks):
            raise ValueError("unexpected end of input")
        t = toks[pos[0]]
        pos[0] += 1
        return t

    def parse(min_bp):
        t = peek()
        if t in ("-", "+"):
            take()
            v = parse(UNARY_BP)
            operand = -v if t == "-" else v
        elif t == "(":
            take()
            operand = parse(0)
            if peek() != ")":
                raise ValueError("expected )")
            take()
        elif t == "n":
            operand = take()[1]
        else:
            raise ValueError("expected an operand, got %r" % (t,))
        while True:
            op = peek()
            if op not in INFIX:
                break
            lbp, rbp = INFIX[op]
            if lbp < min_bp:
                break
            take()
            rhs = parse(rbp)
            if op == "+":
                operand = operand + rhs
            elif op == "-":
                operand = operand - rhs
            elif op == "*":
                operand = operand * rhs
            elif op == "/":
                operand = operand / rhs
            else:
                operand = operand ** rhs
        return operand

    value = parse(0)
    if pos[0] != len(toks):
        raise ValueError("unexpected trailing input")
    if isinstance(value, complex):
        # a negative base with a fractional exponent has no real value
        raise ValueError("result is not real")
    return float(value)
