"""Shortest prefix match for a small pattern language.

Pattern elements (read left to right; each consumes a contiguous chunk of
text, the chunks covering the matched prefix exactly):

  - an ordinary character matches exactly itself
  - '?' matches exactly one character
  - '*' matches zero or more characters
  - '{a,b,c}' matches exactly one of the comma-separated alternatives; each
    alternative is itself a sequence of ordinary characters, '?' and '*'
    (groups never nest)
  - '\\' escapes the following character, making it an ordinary literal
    (a trailing '\\' is an error)

Inside a group alternative an unescaped '{' is an error; the first unescaped
'}' closes the group and unescaped ',' separates alternatives, so literal
braces and commas inside an alternative must be escaped.  An unescaped '}'
with no open group is an error.  Every malformed pattern raises ValueError.
"""


def _parse(pattern):
    """Parse ``pattern`` into a tuple of elements.

    Element encodings:
      ('lit', ch)                    ordinary literal character ch
      ('q',)                         single-character wildcard
      ('star',)                      any string, including the empty one
      ('group', (alt1, alt2, ...))   alternatives; each alt is a tuple of
                                     elements drawn from lit / q / star

    Raises ValueError for every malformed pattern.
    """
    elements = []
    i = 0
    n = len(pattern)
    while i < n:
        ch = pattern[i]
        if ch == '\\':
            if i + 1 >= n:
                raise ValueError("backslash must be followed by a character")
            elements.append(('lit', pattern[i + 1]))
            i += 2
        elif ch == '*':
            elements.append(('star',))
            i += 1
        elif ch == '?':
            elements.append(('q',))
            i += 1
        elif ch == '{':
            alts, i = _scan_group(pattern, i)
            elements.append(('group', alts))
        elif ch == '}':
            raise ValueError("unmatched '}'")
        else:
            elements.append(('lit', ch))
            i += 1
    return tuple(elements)


def _scan_group(pattern, start):
    """``pattern[start]`` is an unescaped '{'.  Scan one group.

    Returns (alternatives, index just past the closing '}`).
    """
    n = len(pattern)
    j = start + 1
    alts = []
    current = []
    while j < n:
        c = pattern[j]
        if c == '\\':
            if j + 1 >= n:
                raise ValueError("backslash must be followed by a character")
            current.append(('lit', pattern[j + 1]))
            j += 2
        elif c == '}':
            alts.append(tuple(current))
            return tuple(alts), j + 1
        elif c == ',':
            alts.append(tuple(current))
            current = []
            j += 1
        elif c == '{':
            raise ValueError("unescaped '{' inside group alternative")
        elif c == '*':
            current.append(('star',))
            j += 1
        elif c == '?':
            current.append(('q',))
            j += 1
        else:
            current.append(('lit', c))
            j += 1
    raise ValueError("unterminated group")


def shortest_prefix_match(pattern, text):
    """Return the smallest L with 0 <= L <= len(text) such that ``pattern``
    matches text[:L]; return -1 when no such L exists.
    """
    elements = _parse(pattern)
    n = len(text)

    # Bit i of the integer ``reach`` is set iff, after the elements processed
    # so far, the match can be sitting at text position i.  Bit operations on
    # Python ints make every step cheap even for 4000-character texts.
    full = (1 << (n + 1)) - 1        # bits 0..n
    advance_mask = full & ~1         # bits 1..n (ends of one-character chunks)

    char_mask = {}
    for idx, ch in enumerate(text):
        char_mask[ch] = char_mask.get(ch, 0) | (1 << (idx + 1))

    def step_lit(s, ch):
        return (s << 1) & char_mask.get(ch, 0)

    def step_q(s):
        return (s << 1) & advance_mask

    def step_star(s):
        # From any start i a star can end at any j >= i, so the set of ends
        # is exactly the interval [min(reachable starts), n].
        low = (s & -s).bit_length() - 1
        return full ^ ((1 << low) - 1)

    def run_sequence(s, seq):
        for el in seq:
            kind = el[0]
            if kind == 'lit':
                s = step_lit(s, el[1])
            elif kind == 'q':
                s = step_q(s)
            else:
                s = step_star(s)
            if not s:
                return 0
        return s

    reach = 1  # position 0 before any element
    for el in elements:
        kind = el[0]
        if kind == 'group':
            start = reach
            reach = 0
            for alt in el[1]:
                reach |= run_sequence(start, alt)
        elif kind == 'lit':
            reach = step_lit(reach, el[1])
        elif kind == 'q':
            reach = step_q(reach)
        else:
            reach = step_star(reach)
        if not reach:
            break
    if not reach:
        return -1
    return (reach & -reach).bit_length() - 1
