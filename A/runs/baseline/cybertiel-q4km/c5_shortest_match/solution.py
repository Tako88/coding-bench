"""shortest_prefix_match: match a pattern against the shortest prefix of text."""


def _parse(pattern):
    """Parse pattern into a list of elements.

    Element forms:
      ('char', c)          matches exactly one char c
      ('question',)        matches exactly one char
      ('star',)            matches zero or more chars
      ('group', alts)      matches one of alts; each alt is a list of ('char'|'question'|'star')
    Raises ValueError on any malformed pattern.
    """
    n = len(pattern)

    def parse_seq(i, terminators):
        """Parse elements until we hit a terminator char or end of string.

        terminators is a set of chars that stop parsing. At top level it is empty
        (parse to end of string). Inside a group it is {'}', ',': '}' closes the
        group and ',' separates alternatives.
        Returns (elements, index_after).
        """
        elements = []
        while i < n:
            c = pattern[i]
            if c in terminators:
                break
            if c == '\\':
                if i + 1 >= n:
                    raise ValueError("dangling backslash")
                elements.append(('char', pattern[i + 1]))
                i += 2
            elif c == '{':
                if '}' in terminators:
                    raise ValueError("'{0}' inside a group".format(c))
                sub, i = parse_group(i)
                elements.append(sub)
            elif c == '}':
                if '}' not in terminators:
                    raise ValueError("unmatched '}'")
                break
            elif c == '?':
                elements.append(('question',))
                i += 1
            elif c == '*':
                elements.append(('star',))
                i += 1
            else:
                elements.append(('char', c))
                i += 1
        return elements, i

    def parse_group(i):
        # pattern[i] == '{'
        i += 1  # skip '{'
        alternatives = []
        while True:
            alts_elements, j = parse_seq(i, {'}', ','})
            if j < n and pattern[j] == ',':
                alternatives.append(alts_elements)
                i = j + 1  # skip ','
                continue
            # expect closing '}'
            alternatives.append(alts_elements)
            if j >= n or pattern[j] != '}':
                raise ValueError("group '{' without closing '}'")
            i = j + 1  # skip '}'
            break
        return ('group', alternatives), i

    elements, pos = parse_seq(0, set())
    return elements


def _transition(el, reachable, text, n_text):
    """Given reachable start positions (set of ints), return reachable end positions."""
    kind = el[0]
    if kind == 'char':
        c = el[1]
        out = set()
        for pos in reachable:
            if pos < n_text and text[pos] == c:
                out.add(pos + 1)
        return out
    if kind == 'question':
        out = set()
        for pos in reachable:
            if pos < n_text:
                out.add(pos + 1)
        return out
    if kind == 'star':
        if not reachable:
            return set()
        lo = min(reachable)
        return set(range(lo, n_text + 1))
    if kind == 'group':
        alts = el[1]
        out = set()
        for alt in alts:
            cur = set(reachable)
            for sub in alt:
                cur = _transition(sub, cur, text, n_text)
                if not cur:
                    break
            out |= cur
        return out
    raise ValueError("unknown element")


def shortest_prefix_match(pattern, text):
    n_text = len(text)
    elements = _parse(pattern)
    reachable = {0}
    for el in elements:
        reachable = _transition(el, reachable, text, n_text)
        if not reachable:
            return -1
    return min(reachable)
