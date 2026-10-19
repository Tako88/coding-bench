"""Shortest prefix pattern match.

Implements ``shortest_prefix_match(pattern, text)``:

Returns the smallest ``L`` (``0 <= L <= len(text)``) such that ``pattern``
matches ``text[:L]`` according to the pattern language described in
TASK.md, or ``-1`` when no such ``L`` exists.  Any malformed pattern
raises ``ValueError``.

Implementation notes
--------------------
The pattern is parsed into a flat sequence of elements:

    ('char', ch)   literal character
    ('?')          exactly one character
    ('*')          zero or more characters
    ('group', alts) one of the comma-separated alternatives; each
                    alternative is a list of elements (no nesting,
                    because braces never nest).

Matching is done with bit-parallel dynamic programming.  ``m`` is a Python
integer used as a bit mask: bit ``p`` is set exactly when the text
prefix ``text[:p]`` can be consumed by the part of the pattern processed
so far.  Every element step only shifts the mask (and, for literal
characters, ANDs it with a precomputed per-character mask), and a star
step turns the mask into the suffix starting at the lowest set bit.
Groups evaluate every alternative from the mask of the group entry and
OR the results together.  All masks fit in ``len(text) + 1`` bits, so
every step is a constant number of C-level big-int operations: the
whole computation is polynomial in pattern size and text length and is
not affected by how many ways the stars can split.
"""

_STAR = 0
_CHAR = 1
_QMARK = 2
_GROUP = 3


def _parse(pattern):
    """Parse *pattern* into a list of elements (see module docstring).

    Raises ``ValueError`` for every malformed pattern.
    """
    n = len(pattern)
    pos = 0

    def parse_group():
        # pos is at an unescaped '{'
        nonlocal pos
        pos += 1  # consume the opening brace
        alts = []
        cur = []
        while True:
            if pos >= n:
                raise ValueError("unterminated group: no closing '}'")
            ch = pattern[pos]
            if ch == '}':
                alts.append(cur)
                pos += 1
                return (_GROUP, alts)
            if ch == ',':
                alts.append(cur)
                cur = []
                pos += 1
            elif ch == '{':
                raise ValueError(
                    "unescaped '{' inside a group alternative")
            elif ch == '\\':
                if pos + 1 >= n:
                    raise ValueError("backslash with no character after it")
                cur.append((_CHAR, pattern[pos + 1]))
                pos += 2
            elif ch == '?':
                cur.append((_QMARK,))
                pos += 1
            elif ch == '*':
                cur.append((_STAR,))
                pos += 1
            else:
                cur.append((_CHAR, ch))
                pos += 1

    elements = []
    while pos < n:
        ch = pattern[pos]
        if ch == '{':
            elements.append(parse_group())
        elif ch == '\\':
            if pos + 1 >= n:
                raise ValueError("backslash with no character after it")
            elements.append((_CHAR, pattern[pos + 1]))
            pos += 2
        elif ch == '?':
            elements.append((_QMARK,))
            pos += 1
        elif ch == '*':
            elements.append((_STAR,))
            pos += 1
        elif ch == '}':
            raise ValueError("unescaped '}' with no open group")
        else:
            elements.append((_CHAR, ch))
            pos += 1
    return elements


def _run(elements, mask, full, char_masks):
    """Apply a sequence of pattern elements to the reachable-position mask.

    *mask* is a bit mask over text positions ``0..len(text)`` (bit ``p``
    set  =>  ``text[:p]`` reachable so far).  Returns the mask after the
    sequence.  Groups are handled here: each alternative is evaluated
    independently from the entry mask and the results are OR-ed.
    """
    for el in elements:
        if not mask:
            break
        kind = el[0]
        if kind == _CHAR:
            # consume exactly one text character equal to el[1]
            mask = (mask << 1) & char_masks.get(el[1], 0)
        elif kind == _QMARK:
            # consume exactly one text character (any)
            mask = (mask << 1) & full
        elif kind == _STAR:
            # the star may consume 0..any characters: everything at or
            # after the lowest reachable position becomes reachable
            low = (mask & -mask).bit_length() - 1
            mask = full ^ ((1 << low) - 1)
        else:  # _GROUP
            acc = 0
            for alt in el[1]:
                acc |= _run(alt, mask, full, char_masks)
            mask = acc
    return mask


def shortest_prefix_match(pattern, text):
    """Return the smallest L with 0 <= L <= len(text) such that *pattern*
    matches ``text[:L]``, or -1 when there is no such L.

    Malformed patterns raise ``ValueError``.
    """
    elements = _parse(pattern)

    tlen = len(text)
    full = (1 << (tlen + 1)) - 1
    # char_masks[ch]: bit p set iff p >= 1 and text[p-1] == ch.
    char_masks = {}
    for i, ch in enumerate(text):
        char_masks[ch] = char_masks.get(ch, 0) | (1 << (i + 1))

    mask = _run(elements, 1, full, char_masks)
    if not mask:
        return -1
    return (mask & -mask).bit_length() - 1
