"""Reference implementations and brute-force oracles for benchmark C.

The grader's own answers. Never shown to the model.
checks.py uses these for large cases and random cross-checks; validate.py uses
them to calibrate the checkers against independent oracles (shlex, csv, eval).
"""

# ---------------------------------------------------------------- c1 csv


def ref_csv(line):
    fields = []
    i, n = 0, len(line)
    if n == 0:
        return [""]
    while True:
        if line[i] == '"':
            i += 1
            buf = []
            while True:
                if i >= n:
                    raise ValueError("unterminated quoted field")
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        buf.append('"')
                        i += 2
                        continue
                    i += 1
                    break
                buf.append(line[i])
                i += 1
            if i < n and line[i] != ",":
                raise ValueError("characters after closing quote")
            fields.append("".join(buf))
        else:
            j = i
            while j < n and line[j] != ",":
                j += 1
            fields.append(line[i:j])
            i = j
        if i >= n:
            return fields
        i += 1
        if i >= n:
            fields.append("")
            return fields


# ---------------------------------------------------------------- c2 expr


def ref_evaluate(expr):
    toks = []
    i, n = 0, len(expr)
    while i < n:
        c = expr[i]
        if c == " ":
            i += 1
            continue
        if c.isdigit():
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
            toks.append(("num", float(expr[i:j])))
            i = j
            continue
        if c == ".":
            raise ValueError("digit required before dot")
        if c in "+-*/^()":
            toks.append((c, None))
            i += 1
            continue
        raise ValueError("invalid character %r" % (c,))
    pos = [0]

    def peek():
        return toks[pos[0]][0] if pos[0] < len(toks) else None

    def take():
        if pos[0] >= len(toks):
            raise ValueError("unexpected end of input")
        t = toks[pos[0]]
        pos[0] += 1
        return t

    def expr_():
        v = term()
        while peek() in ("+", "-"):
            op = take()[0]
            r = term()
            v = v + r if op == "+" else v - r
        return v

    def term():
        v = unary()
        while peek() in ("*", "/"):
            op = take()[0]
            r = unary()
            v = v * r if op == "*" else v / r
        return v

    def unary():
        if peek() in ("+", "-"):
            op = take()[0]
            v = unary()
            return v if op == "+" else -v
        return power()

    def power():
        base = primary()
        if peek() == "^":
            take()
            return base ** unary()
        return base

    def primary():
        t = take()
        if t[0] == "num":
            return t[1]
        if t[0] == "(":
            v = expr_()
            if peek() != ")":
                raise ValueError("expected )")
            take()
            return v
        raise ValueError("unexpected token %r" % (t[0],))

    v = expr_()
    if pos[0] != len(toks):
        raise ValueError("unexpected trailing input")
    return float(v)


# ---------------------------------------------------------------- c3 tokenize


def ref_tokenize(line):
    out = []
    n = len(line)
    i = 0
    cur = None

    def start():
        nonlocal cur
        if cur is None:
            cur = []

    while i < n:
        c = line[i]
        if c == " " or c == "\t":
            if cur is not None:
                out.append("".join(cur))
                cur = None
            i += 1
            continue
        if c == "#" and cur is None:
            break
        start()
        if c == "\\":
            if i + 1 >= n:
                raise ValueError("backslash with no character after it")
            cur.append(line[i + 1])
            i += 2
            continue
        if c == "'":
            j = line.find("'", i + 1)
            if j < 0:
                raise ValueError("unterminated single quoted string")
            cur.append(line[i + 1:j])
            i = j + 1
            continue
        if c == '"':
            i += 1
            buf = []
            while True:
                if i >= n:
                    raise ValueError("unterminated double quoted string")
                ch = line[i]
                if ch == '"':
                    i += 1
                    break
                if ch == "\\":
                    if i + 1 < n and line[i + 1] in '"\\':
                        buf.append(line[i + 1])
                        i += 2
                        continue
                    buf.append("\\")
                    i += 1
                    continue
                buf.append(ch)
                i += 1
            cur.append("".join(buf))
            continue
        cur.append(c)
        i += 1
    if cur is not None:
        out.append("".join(cur))
    return out


# ---------------------------------------------------------------- c4 schedule


def ref_schedule(intervals):
    import bisect

    n = len(intervals)
    if n == 0:
        return (0, [])
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], i))
    starts = [intervals[i][0] for i in order]
    # P[k], C[k] = best (profit, count) using order[k:], i.e. all starts >= starts[k]
    P = [0] * (n + 1)
    C = [0] * (n + 1)
    for k in range(n - 1, -1, -1):
        i = order[k]
        s, e, p = intervals[i]
        j = bisect.bisect_left(starts, e, k + 1)
        cp, cc = p + P[j], 1 + C[j]
        if cp > P[k + 1] or (cp == P[k + 1] and cc < C[k + 1]):
            P[k], C[k] = cp, cc
        else:
            P[k], C[k] = P[k + 1], C[k + 1]
    total, count = P[0], C[0]
    after = []
    for i in range(n):
        s, e, p = intervals[i]
        j = bisect.bisect_left(starts, e)
        after.append((P[j], C[j]))
    scan = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], intervals[i][2], i))
    chosen = []
    t = 0
    rem_p, rem_c = total, count
    for i in scan:
        if rem_p == 0:
            break
        s, e, p = intervals[i]
        if s < t:
            continue
        hp, hc = after[i]
        if p + hp == rem_p and 1 + hc == rem_c:
            chosen.append((s, e, p))
            t = e
            rem_p -= p
            rem_c -= 1
    return (total, chosen)


def brute_schedule(intervals):
    n = len(intervals)
    best = None
    for mask in range(1 << n):
        sel = [i for i in range(n) if (mask >> i) & 1]
        ok = True
        for a in range(len(sel)):
            for b in range(a + 1, len(sel)):
                s1, e1, _ = intervals[sel[a]]
                s2, e2, _ = intervals[sel[b]]
                if not (e1 <= s2 or e2 <= s1):
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        p = sum(intervals[i][2] for i in sel)
        lst = sorted((tuple(intervals[i]) for i in sel), key=lambda x: (x[0], x[1], x[2]))
        key = (-p, len(sel), lst)
        if best is None or key < best:
            best = key
    return (-best[0], best[2])


# ---------------------------------------------------------------- c5 matcher


def compile_pattern(pat):
    """Compile to a flat NFA. op kinds: char / any / star / split / jmp / accept."""
    ops = []

    def seq(i, stop_at_brace):
        while i < len(pat):
            c = pat[i]
            if stop_at_brace and (c == "}" or c == ","):
                return i
            if c == "\\":
                if i + 1 >= len(pat):
                    raise ValueError("backslash with no character after it")
                ops.append({"k": "char", "c": pat[i + 1]})
                i += 2
                continue
            if c == "?":
                ops.append({"k": "any"})
                i += 1
                continue
            if c == "*":
                ops.append({"k": "star"})
                i += 1
                continue
            if c == "{":
                if stop_at_brace:
                    raise ValueError("groups do not nest")
                split_at = len(ops)
                ops.append({"k": "split", "targets": []})
                i += 1
                branches = []
                while True:
                    b_start = len(ops)
                    i = seq(i, True)
                    b_end = len(ops)
                    ops.append({"k": "jmp", "target": None})
                    branches.append((b_start, b_end, len(ops) - 1))
                    if i >= len(pat):
                        raise ValueError("unterminated group")
                    if pat[i] == ",":
                        i += 1
                        continue
                    if pat[i] == "}":
                        i += 1
                        break
                    raise ValueError("bad group")
                join = len(ops)
                ops[split_at]["targets"] = [b[0] for b in branches]
                for (_s, _e, j) in branches:
                    ops[j]["target"] = join
                continue
            if c == "}":
                raise ValueError("unmatched }")
            ops.append({"k": "char", "c": c})
            i += 1
        if stop_at_brace:
            raise ValueError("unterminated group")
        return i

    seq(0, False)
    ops.append({"k": "accept"})
    return ops


def ref_shortest(pattern, text):
    ops = compile_pattern(pattern)
    acc = len(ops) - 1

    def closure(states):
        seen = set()
        stack = list(states)
        while stack:
            s = stack.pop()
            if s in seen:
                continue
            seen.add(s)
            op = ops[s]
            k = op["k"]
            if k == "star":
                stack.append(s + 1)
            elif k == "split":
                stack.extend(op["targets"])
            elif k == "jmp":
                stack.append(op["target"])
        return seen

    cur = closure({0})
    for L in range(len(text) + 1):
        if acc in cur:
            return L
        if L == len(text):
            break
        ch = text[L]
        nxt = set()
        for s in cur:
            op = ops[s]
            k = op["k"]
            if k == "char" and op["c"] == ch:
                nxt.add(s + 1)
            elif k == "any":
                nxt.add(s + 1)
            elif k == "star":
                nxt.add(s)
        cur = closure(nxt)
    return -1


def parse_elements(pat):
    i = 0

    def seq(stop):
        nonlocal i
        out = []
        while i < len(pat):
            c = pat[i]
            if stop and (c == "}" or c == ","):
                return out
            if c == "\\":
                if i + 1 >= len(pat):
                    raise ValueError("backslash with no character after it")
                out.append(("c", pat[i + 1]))
                i += 2
                continue
            if c == "?":
                out.append(("q",))
                i += 1
                continue
            if c == "*":
                out.append(("s",))
                i += 1
                continue
            if c == "{":
                if stop:
                    raise ValueError("groups do not nest")
                i += 1
                branches = []
                while True:
                    branches.append(seq(True))
                    if i >= len(pat):
                        raise ValueError("unterminated group")
                    if pat[i] == ",":
                        i += 1
                        continue
                    if pat[i] == "}":
                        i += 1
                        break
                    raise ValueError("bad group")
                out.append(("g", branches))
                continue
            if c == "}":
                raise ValueError("unmatched }")
            out.append(("c", c))
            i += 1
        if stop:
            raise ValueError("unterminated group")
        return out

    return seq(False)


def brute_positions(elems, text, ti):
    """Every position reachable by matching the whole element list from ti."""
    res = set()

    def rec(ei, p):
        if ei == len(elems):
            res.add(p)
            return
        e = elems[ei]
        k = e[0]
        if k == "c":
            if p < len(text) and text[p] == e[1]:
                rec(ei + 1, p + 1)
        elif k == "q":
            if p < len(text):
                rec(ei + 1, p + 1)
        elif k == "s":
            for nxt in range(p, len(text) + 1):
                rec(ei + 1, nxt)
        elif k == "g":
            for b in e[1]:
                for q in brute_positions(b, text, p):
                    rec(ei + 1, q)

    rec(0, ti)
    return res


def brute_shortest(pattern, text):
    elems = parse_elements(pattern)
    ps = brute_positions(elems, text, 0)
    return min(ps) if ps else -1
