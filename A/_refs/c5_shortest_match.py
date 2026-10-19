"""Reference solution for c5_shortest_match.

Forward reachability: keep the set of text positions reachable after matching
the pattern elements seen so far. '*' contributes every position from here to
the end of the text, and a group contributes the reachable positions of each of
its alternatives, so no backtracking is needed.
"""


def _parse(pat):
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
            elif c == "?":
                out.append(("q",))
                i += 1
            elif c == "*":
                out.append(("s",))
                i += 1
            elif c == "{":
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
            elif c == "}":
                raise ValueError("unmatched }")
            else:
                out.append(("c", c))
                i += 1
        if stop:
            raise ValueError("unterminated group")
        return out

    return seq(False)


def _reach(elems, start, n, text):
    """every position reachable after matching the whole element list from start"""
    cur = {start}
    for e in elems:
        kind = e[0]
        nxt = set()
        if kind == "c":
            for p in cur:
                if p < n and text[p] == e[1]:
                    nxt.add(p + 1)
        elif kind == "q":
            for p in cur:
                if p < n:
                    nxt.add(p + 1)
        elif kind == "s":
            for p in cur:
                nxt.update(range(p, n + 1))
        else:
            for p in cur:
                for branch in e[1]:
                    nxt.update(_reach(branch, p, n, text))
        cur = nxt
        if not cur:
            break
    return cur


def shortest_prefix_match(pattern, text):
    elems = _parse(pattern)
    n = len(text)
    reachable = _reach(elems, 0, n, text)
    return min(reachable) if reachable else -1
