"""Shortest prefix match for a small glob-like pattern language.

Pattern language (see TASK.md):
  - ordinary character      matches exactly itself
  - '?'                     matches exactly one character
  - '*'                     matches zero or more characters
  - '{a,b,...}'             group: matches exactly one of its comma separated
                            alternatives (alternatives may be empty, and may
                            contain ordinary chars, '?' and '*'; braces never
                            nest)
  - '\\' escapes the next character (so \\* \\? \\{ \\} \\, \\| match themselves)

Every malformed pattern raises ValueError.

shortest_prefix_match returns the SMALLEST L with 0 <= L <= len(text) such
that the pattern matches text[:L], or -1 if no such L exists.

Implementation: the pattern is compiled to an NFA (epsilon transitions form a
DAG) and the NFA is simulated once over the text, so the running time is
linear in len(text) (times a small number of NFA states) -- no exponential
backtracking over the splits of each '*'.
"""

from typing import Dict, List, Tuple


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def _parse_seq(pattern: str, i: int, in_group: bool):
    """Parse a sequence of elements starting at index i.

    Returns (elements, index) where index is either len(pattern) (when not
    inside a group) or the position of the unescaped '}' that should close
    the current group.  Raises ValueError for malformed patterns.
    """
    elems: List[Tuple] = []
    n = len(pattern)
    while i < n:
        c = pattern[i]
        if c == '\\':
            if i + 1 >= n:
                raise ValueError("pattern ends with a dangling backslash")
            elems.append(('lit', pattern[i + 1]))
            i += 2
        elif c == '?':
            elems.append(('any',))
            i += 1
        elif c == '*':
            elems.append(('star',))
            i += 1
        elif c == '{':
            if in_group:
                raise ValueError("unescaped '{' inside a group alternative")
            elem, i = _parse_group(pattern, i)
            elems.append(elem)
        elif c == '}' or (in_group and c == ','):
            if in_group:
                # stop at the ',' that separates alternatives, or at the
                # '}' that closes the group; the caller handles it
                return elems, i
            raise ValueError("unescaped '}' with no open group")
        else:
            elems.append(('lit', c))
            i += 1
    if in_group:
        raise ValueError("group is missing its closing '}'")
    return elems, i


def _parse_group(pattern: str, i: int):
    """Parse a group starting at pattern[i] == '{'. Returns (elem, index)."""
    i += 1  # skip '{'
    alternatives: List[List[Tuple]] = []
    while True:
        elems, j = _parse_seq(pattern, i, True)
        alternatives.append(elems)
        if j >= len(pattern):  # unreachable: _parse_seq raises first
            raise ValueError("group is missing its closing '}'")
        if pattern[j] == '}':
            return ('group', alternatives), j + 1
        # pattern[j] == ',' -> next alternative
        i = j + 1


# --------------------------------------------------------------------------
# NFA construction
# --------------------------------------------------------------------------

def _build_nfa(elements: List[Tuple]):
    """Build an NFA for the element sequence.

    Returns (start, accept, eps, trans, any_trans) where
      eps[s]       list of epsilon targets
      trans[s]     dict mapping a literal character -> list of targets
      any_trans[s] list of targets for a "match any character" transition
    """
    eps: List[List[int]] = []
    trans: List[Dict[str, List[int]]] = []
    any_trans: List[List[int]] = []

    def new_state() -> int:
        eps.append([])
        trans.append({})
        any_trans.append([])
        return len(eps) - 1

    def build_seq(seq: List[Tuple]):
        entry = new_state()
        cur = entry
        for el in seq:
            e, x = build_el(el)
            eps[cur].append(e)
            cur = x
        return entry, cur

    def build_el(el: Tuple):
        kind = el[0]
        if kind == 'lit':
            s = new_state()
            t = new_state()
            trans[s].setdefault(el[1], []).append(t)
            return s, t
        if kind == 'any':
            s = new_state()
            t = new_state()
            any_trans[s].append(t)
            return s, t
        if kind == 'star':
            s = new_state()
            t = new_state()
            any_trans[s].append(s)   # consume one character, stay in s
            eps[s].append(t)         # ... or stop here (zero or more)
            return s, t
        if kind == 'group':
            entry = new_state()
            exit_ = new_state()
            for alt in el[1]:
                if not alt:
                    eps[entry].append(exit_)
                else:
                    e, x = build_seq(alt)
                    eps[entry].append(e)
                    eps[x].append(exit_)
            return entry, exit_
        raise AssertionError("unknown element kind %r" % (kind,))

    start, accept = build_seq(elements)
    return start, accept, eps, trans, any_trans


def _epsilon_closures(eps: List[List[int]]) -> List[int]:
    """For every state, a bitmask of the states reachable by epsilon moves
    (including itself).  The epsilon graph produced by the construction above
    is acyclic, so an iterative post-order pass is safe."""
    n = len(eps)
    closure = [0] * n
    for root in range(n):
        if closure[root]:
            continue
        stack = [(root, False)]
        while stack:
            u, expanded = stack.pop()
            if expanded:
                m = 1 << u
                for v in eps[u]:
                    m |= closure[v]
                closure[u] = m
            elif closure[u]:
                continue
            else:
                stack.append((u, True))
                for v in eps[u]:
                    if not closure[v]:
                        stack.append((v, False))
    return closure


# --------------------------------------------------------------------------
# Matching
# --------------------------------------------------------------------------

def shortest_prefix_match(pattern: str, text: str) -> int:
    elements, _ = _parse_seq(pattern, 0, False)
    start, accept, eps, trans, any_trans = _build_nfa(elements)
    closure = _epsilon_closures(eps)

    # goto masks: for each state, per literal character, the epsilon-closed
    # set of states reachable by consuming that character.
    goto: List[Dict[str, int]] = []
    any_goto: List[int] = []
    for s in range(len(eps)):
        g: Dict[str, int] = {}
        for c, targets in trans[s].items():
            m = 0
            for t in targets:
                m |= closure[t]
            g[c] = m
        goto.append(g)
        m = 0
        for t in any_trans[s]:
            m |= closure[t]
        any_goto.append(m)

    accept_bit = 1 << accept
    cur = closure[start]

    n = len(text)
    for L in range(n + 1):
        if cur & accept_bit:
            return L
        if L == n:
            break
        c = text[L]
        nxt = 0
        m = cur
        while m:
            low = m & -m
            s = low.bit_length() - 1
            m ^= low
            g = goto[s]
            if g:
                nxt |= g.get(c, 0)
            nxt |= any_goto[s]
        cur = nxt
        if not cur:
            break
    return -1
