def shortest_prefix_match(pattern, text):
    """Return the smallest L (0 <= L <= len(text)) such that the pattern
    matches text[:L], or -1 if no such L exists. Raises ValueError on
    malformed patterns."""
    elems = _parse(pattern)

    # NFA construction (Thompson-style).
    eps = []       # eps[i] -> list of target states (epsilon transitions)
    trans = []     # trans[i] -> dict char -> list of target states
    anytr = []     # anytr[i] -> list of target states (for '?', any single char)

    def new_state():
        eps.append([])
        trans.append({})
        anytr.append([])
        return len(eps) - 1

    def add_eps(a, b):
        eps[a].append(b)

    def add_char(a, c, b):
        lst = trans[a].get(c)
        if lst is None:
            lst = trans[a][c] = []
        lst.append(b)

    def add_any(a, b):
        anytr[a].append(b)

    def build_char(c):
        inp = new_state()
        out = new_state()
        add_char(inp, c, out)
        return inp, out

    def build_any():
        inp = new_state()
        out = new_state()
        add_any(inp, out)
        return inp, out

    def build_star():
        # Matches zero or more of any character.
        inp = new_state()
        loop = new_state()
        out = new_state()
        add_eps(inp, out)   # zero characters
        add_eps(inp, loop)  # enter consumption loop
        add_eps(loop, out)  # leave consumption loop
        add_any(loop, loop) # consume one character, stay in loop
        return inp, out

    def build_group(alternatives):
        inp = new_state()
        out = new_state()
        for alt in alternatives:
            alt_in, alt_out = build_concat(alt)
            add_eps(inp, alt_in)
            add_eps(alt_out, out)
        return inp, out

    def build_concat(elems):
        if not elems:
            s = new_state()
            return s, s
        inp = None
        prev_out = None
        for e in elems:
            e_in, e_out = build_elem(e)
            if inp is None:
                inp = e_in
            else:
                add_eps(prev_out, e_in)
            prev_out = e_out
        return inp, prev_out

    def build_elem(e):
        kind = e[0]
        if kind == 'char':
            return build_char(e[1])
        if kind == 'any':
            return build_any()
        if kind == 'star':
            return build_star()
        if kind == 'group':
            return build_group(e[1])
        raise ValueError("unknown element")

    start, accept = build_concat(elems)

    # Epsilon closure (iterative, handles cycles).
    def eps_closure(states):
        visited = set(states)
        stack = list(states)
        while stack:
            s = stack.pop()
            for t in eps[s]:
                if t not in visited:
                    visited.add(t)
                    stack.append(t)
        return visited

    current = eps_closure({start})
    if accept in current:
        return 0
    for i, ch in enumerate(text, 1):
        nxt = set()
        for s in current:
            lst = trans[s].get(ch)
            if lst:
                nxt.update(lst)
            for t in anytr[s]:
                nxt.add(t)
        if not nxt:
            return -1
        current = eps_closure(nxt)
        if accept in current:
            return i
    return -1


def _parse(pattern):
    """Parse a pattern string into a list of top-level elements.
    Raises ValueError on any malformed pattern."""
    n = len(pattern)
    pos = 0

    def parse_elem(in_group):
        nonlocal pos
        if pos >= n:
            raise ValueError("unexpected end of pattern")
        c = pattern[pos]
        if c == '\\':
            pos += 1
            if pos >= n:
                raise ValueError("trailing backslash")
            ch = pattern[pos]
            pos += 1
            return ('char', ch)
        if c == '?':
            pos += 1
            return ('any',)
        if c == '*':
            pos += 1
            return ('star',)
        if c == '{':
            if in_group:
                raise ValueError("unescaped brace inside group")
            return parse_group()
        if c == '}':
            raise ValueError("unescaped brace")
        # Ordinary character (',' is ordinary outside a group).
        pos += 1
        return ('char', c)

    def parse_group():
        nonlocal pos
        # pattern[pos] == '{'
        pos += 1
        alternatives = []
        while True:
            alt = parse_seq({',', '}'}, True)
            alternatives.append(alt)
            if pos >= n:
                raise ValueError("unterminated group")
            if pattern[pos] == ',':
                pos += 1
                continue
            if pattern[pos] == '}':
                pos += 1
                break
            raise ValueError("unexpected character in group")
        return ('group', alternatives)

    def parse_seq(stop, in_group):
        elems = []
        while pos < n and pattern[pos] not in stop:
            elems.append(parse_elem(in_group))
        return elems

    elems = parse_seq(set(), False)
    if pos != n:
        raise ValueError("unexpected character")
    return elems
