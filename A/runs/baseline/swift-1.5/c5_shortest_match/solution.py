"""Shortest prefix pattern match.

Implements shortest_prefix_match(pattern, text) per TASK.md.

Approach: parse the pattern into atoms (literal / '?' / '*' / group), then
compute the set of reachable text positions with a bitset DP.  Bit j of the
bitset means "position j in text is reachable after the processed prefix of
the pattern".  Transitions:

  literal c : ((dp & mask_of_c) << 1) & full
  '?'       : (dp << 1) & full
  '*'       : upward closure of dp == all positions >= min(dp)
  group     : union, over alternatives, of the alternative's end positions

The '*' transition is O(1) per star, so the whole match is
O(num_atoms * bitset_ops) -- well within the performance budget
(20 stars, 4000 chars of text).
"""

__all__ = ["shortest_prefix_match"]


def _parse(pattern):
    """Parse *pattern* into a flat list of atoms.

    Atoms are tuples:
        ('lit', ch)  literal character
        ('q',)       '?'
        ('s',)       '*'
        ('grp', [alt, ...])  group; each alt is a list of non-group atoms

    Raises ValueError for any malformed pattern.
    """
    n = len(pattern)
    i = 0

    def parse_alt():
        """Parse one group alternative, stopping at the first unescaped
        ',' or '}' (both are consumed).  An unescaped '{' or end of
        input is an error."""
        nonlocal i
        atoms = []
        while i < n:
            ch = pattern[i]
            if ch == '\\':
                if i + 1 >= n:
                    raise ValueError("dangling backslash in pattern")
                atoms.append(('lit', pattern[i + 1]))
                i += 2
            elif ch == '{':
                raise ValueError("unescaped '{' inside a group is not allowed")
            elif ch == ',' or ch == '}':
                term = ch
                i += 1
                return atoms, term
            elif ch == '?':
                atoms.append(('q',))
                i += 1
            elif ch == '*':
                atoms.append(('s',))
                i += 1
            else:
                atoms.append(('lit', ch))
                i += 1
        raise ValueError("unterminated group")

    atoms = []
    while i < n:
        ch = pattern[i]
        if ch == '\\':
            if i + 1 >= n:
                raise ValueError("dangling backslash in pattern")
            atoms.append(('lit', pattern[i + 1]))
            i += 2
        elif ch == '}':
            raise ValueError("unmatched '}'")
        elif ch == '{':
            i += 1
            alt, term = parse_alt()
            alts = [alt]
            while term == ',':
                alt, term = parse_alt()
                alts.append(alt)
            atoms.append(('grp', alts))
        elif ch == '?':
            atoms.append(('q',))
            i += 1
        elif ch == '*':
            atoms.append(('s',))
            i += 1
        else:
            atoms.append(('lit', ch))
            i += 1
    return atoms


def shortest_prefix_match(pattern, text):
    """Return the smallest L with 0 <= L <= len(text) such that *pattern*
    matches text[:L], or -1 if no such L exists.

    Raises ValueError for a malformed *pattern*.
    """
    atoms = _parse(pattern)
    n = len(text)
    full = (1 << (n + 1)) - 1  # bits 0..n all set

    char_pos = {}
    for j, ch in enumerate(text):
        char_pos[ch] = char_pos.get(ch, 0) | (1 << j)

    def step(dp, a):
        """Advance the reachable-position bitset *dp* by one atom *a*."""
        k = a[0]
        if k == 'lit':
            return ((dp & char_pos.get(a[1], 0)) << 1) & full
        if k == 'q':
            return (dp << 1) & full
        if k == 's':
            if dp == 0:
                return 0
            # '*' from position j reaches every j' >= j, so the result is
            # every position >= min(dp).
            minj = (dp & -dp).bit_length() - 1
            return full & ~((1 << minj) - 1)
        # group: union of the alternatives' end positions
        res = 0
        for alt in a[1]:
            cur = dp
            for b in alt:
                cur = step(cur, b)
                if cur == 0:
                    break
            res |= cur
        return res

    dp = 1  # bit 0 set: position 0 reachable before any atom
    for a in atoms:
        dp = step(dp, a)
        if dp == 0:
            return -1
    return (dp & -dp).bit_length() - 1
