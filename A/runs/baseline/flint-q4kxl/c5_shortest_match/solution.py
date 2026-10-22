"""Shortest prefix pattern match."""


def _parse(pattern):
    """Parse a pattern into a list of elements.

    Element forms:
        ('lit', ch)   - ordinary character (possibly escaped)
        ('any',)      - '?'
        ('star',)     - '*'
        ('group', [list_of_alternatives])
                     - '{...}' with a list of alternative element-lists
    Raises ValueError on any malformed pattern.
    """
    elems = []
    n = len(pattern)
    i = 0
    while i < n:
        ch = pattern[i]
        if ch == '\\':
            if i + 1 >= n:
                raise ValueError("pattern ends with a lone backslash")
            elems.append(('lit', pattern[i + 1]))
            i += 2
        elif ch == '?':
            elems.append(('any',))
            i += 1
        elif ch == '*':
            elems.append(('star',))
            i += 1
        elif ch == '{':
            j = i + 1
            closed = False
            while j < n:
                c = pattern[j]
                if c == '\\':
                    j += 2
                    continue
                if c == '{':
                    raise ValueError("nested group is not allowed")
                if c == '}':
                    closed = True
                    break
                j += 1
            if not closed:
                raise ValueError("unclosed group")
            content = pattern[i + 1:j]
            alts = []
            cur = []
            k = 0
            m = len(content)
            while k < m:
                c = content[k]
                if c == '\\':
                    cur.append(('lit', content[k + 1]))
                    k += 2
                elif c == ',':
                    alts.append(cur)
                    cur = []
                    k += 1
                elif c == '?':
                    cur.append(('any',))
                    k += 1
                elif c == '*':
                    cur.append(('star',))
                    k += 1
                elif c == '{':
                    raise ValueError("nested group is not allowed")
                elif c == '}':
                    raise ValueError("unexpected close brace")
                else:
                    cur.append(('lit', c))
                    k += 1
            alts.append(cur)
            elems.append(('group', alts))
            i = j + 1
        elif ch == '}':
            raise ValueError("unmatched close brace")
        else:
            elems.append(('lit', ch))
            i += 1
    return elems


def shortest_prefix_match(pattern, text):
    elems = _parse(pattern)

    trans = []

    def new_state():
        trans.append([])
        return len(trans) - 1

    def build_elem(e):
        if e[0] == 'lit':
            s = new_state()
            t = new_state()
            trans[s].append(('lit', e[1], t))
            return s, t
        if e[0] == 'any':
            s = new_state()
            t = new_state()
            trans[s].append(('any', t))
            return s, t
        if e[0] == 'star':
            s = new_state()
            t = new_state()
            trans[s].append(('e', t))
            trans[s].append(('any', s))
            trans[t].append(('e', s))
            return s, t
        # group
        gs = new_state()
        ge = new_state()
        for alt in e[1]:
            s, t = build_list(alt)
            trans[gs].append(('e', s))
            trans[t].append(('e', ge))
        return gs, ge

    def build_list(elems):
        if not elems:
            s = new_state()
            return s, s
        s, t = build_elem(elems[0])
        for e in elems[1:]:
            s2, t2 = build_elem(e)
            trans[t].append(('e', s2))
            t = t2
        return s, t

    start, accept = build_list(elems)

    def closure(states):
        seen = set(states)
        stack = list(states)
        while stack:
            s = stack.pop()
            for tr in trans[s]:
                if tr[0] == 'e':
                    t = tr[1]
                    if t not in seen:
                        seen.add(t)
                        stack.append(t)
        return seen

    cur = closure({start})
    if accept in cur:
        return 0
    for idx, ch in enumerate(text):
        nxt = set()
        for s in cur:
            for tr in trans[s]:
                kind = tr[0]
                if kind == 'e':
                    nxt.add(tr[1])
                elif kind == 'any':
                    nxt.add(tr[1])
                else:  # 'lit'
                    if ch == tr[1]:
                        nxt.add(tr[2])
        cur = closure(nxt)
        if accept in cur:
            return idx + 1
    return -1
