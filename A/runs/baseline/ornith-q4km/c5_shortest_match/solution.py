"""shortest prefix pattern match.

Implement shortest_prefix_match(pattern, text).
"""


class _PatternError(ValueError):
    pass


# Element representations (tuples):
#   ('char', c)          ordinary literal character
#   ('q',)               '?' matches exactly one character
#   ('star',)            '*' matches zero or more characters
#   ('group', [alts])    each alt is a list of elements; matches one alternative


def _parse(pattern):
    """Parse pattern into a list of elements. Raise ValueError on malformed input."""
    elems, pos = _parse_seq(pattern, 0, False)
    if pos != len(pattern):
        raise _PatternError("trailing characters")
    return elems


def _parse_seq(pattern, pos, in_group):
    elements = []
    n = len(pattern)
    while pos < n:
        c = pattern[pos]
        if c == '}':
            if not in_group:
                raise _PatternError("stray '}'")
            return elements, pos  # leave pos at the closing '}'
        if c == ',' and in_group:
            return elements, pos  # separator; caller consumes it
        if c == '{' and in_group:
            raise _PatternError("unescaped '{' inside group")
        elem, pos = _parse_element(pattern, pos, in_group)
        elements.append(elem)
    if in_group:
        raise _PatternError("unterminated group")
    return elements, pos


def _parse_element(pattern, pos, in_group):
    n = len(pattern)
    c = pattern[pos]
    if c == '\\':
        if pos + 1 >= n:
            raise _PatternError("trailing backslash")
        return ('char', pattern[pos + 1]), pos + 2
    if c == '{':
        return _parse_group(pattern, pos)
    if c == '*':
        return ('star',), pos + 1
    if c == '?':
        return ('q',), pos + 1
    if c == '}' and not in_group:
        raise _PatternError("stray '}'")
    return ('char', c), pos + 1


def _parse_group(pattern, pos):
    n = len(pattern)
    pos += 1  # skip opening '{'
    alts = []
    while True:
        cur, pos = _parse_seq(pattern, pos, True)
        alts.append(cur)
        if pos >= n:
            raise _PatternError("unterminated group")
        c = pattern[pos]
        if c == '}':
            pos += 1
            return ('group', alts), pos
        if c == ',':
            pos += 1
            continue
        raise _PatternError("expected ',' or '}' in group")


def _star_closure(x, n, full):
    """newmask[p] = OR_{q<=p} oldmask[q] (a '*' consumes text[q:p], any length)."""
    x &= full
    shift = 1
    while shift <= n:
        x = x | (x << shift)
        shift *= 2
    return x & full


def _transition(elem, reach, charmask, n, full):
    kind = elem[0]
    if kind == 'char':
        cm = charmask.get(elem[1], 0)
        return ((reach & cm) << 1) & full
    if kind == 'q':
        return (reach << 1) & full
    if kind == 'star':
        return _star_closure(reach, n, full)
    # group
    res = 0
    for alt in elem[1]:
        res |= _match_seq(alt, reach, charmask, n, full)
    return res & full


def _match_seq(seq, reach, charmask, n, full):
    for elem in seq:
        reach = _transition(elem, reach, charmask, n, full)
    return reach


def shortest_prefix_match(pattern, text):
    elems = _parse(pattern)
    n = len(text)
    full = (1 << (n + 1)) - 1
    charmask = {}
    for i, ch in enumerate(text):
        charmask[ch] = charmask.get(ch, 0) | (1 << i)

    reach = 1  # bit 0: empty prefix matched
    for elem in elems:
        reach = _transition(elem, reach, charmask, n, full)

    if reach == 0:
        return -1
    return (reach & -reach).bit_length() - 1
