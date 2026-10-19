def parse_pattern(pattern):
    """Parse a pattern string into a tuple of elements.

    Each element is:
      - ('char', value) for ordinary characters and escaped characters
      - ('star',) for '*'
      - ('question',) for '?'
      - ('group', alternatives) for '{...}' groups, where alternatives is a tuple of element tuples
    """

    def parse_group(start):
        j = start + 1
        alternatives = []
        alt_start = j
        while True:
            if j >= len(pattern):
                raise ValueError("unclosed group")
            c = pattern[j]
            if c == '\\':
                j += 2
                continue
            if c == ',':
                alternatives.append(parse_alternative(alt_start, j))
                j += 1
                alt_start = j
            elif c == '}':
                alternatives.append(parse_alternative(alt_start, j))
                return (tuple(alternatives), j + 1)
            else:
                j += 1

    def parse_alternative(start, end):
        elements = []
        i = start
        while i < end:
            c = pattern[i]
            if c == '\\':
                if i + 1 >= len(pattern):
                    raise ValueError("backslash without character")
                elements.append(('char', pattern[i + 1]))
                i += 2
            elif c == '{':
                group_alt, next_i = parse_group(i)
                elements.append(('group', group_alt))
                i = next_i
            else:
                elements.append(('char', c))
                i += 1
        return tuple(elements)

    elements = []
    i = 0
    n = len(pattern)
    while i < n:
        c = pattern[i]
        if c == '\\':
            if i + 1 >= n:
                raise ValueError("backslash without character")
            elements.append(('char', pattern[i + 1]))
            i += 2
        elif c == '{':
            group_elems, next_i = parse_group(i)
            elements.append(('group', group_elems))
            i = next_i
        elif c == '*':
            elements.append(('star',))
            i += 1
        elif c == '?':
            elements.append(('question',))
            i += 1
        else:
            elements.append(('char', c))
            i += 1
    return tuple(elements)


def _match_alt(alt, text_idx, text):
    """Match a sequence of elements `alt` (a tuple) against text[text_idx:].
    Returns the new text index if successful, None otherwise."""

    def backtrack(alt_idx, i):
        if alt_idx == len(alt):
            return i
        elem = alt[alt_idx]
        if elem[0] == 'char':
            if i >= len(text) or text[i] != elem[1]:
                return None
            return backtrack(alt_idx + 1, i + 1)
        elif elem[0] == '?':
            if i >= len(text):
                return None
            return backtrack(alt_idx + 1, i + 1)
        elif elem[0] == '*':
            # star: zero or more characters
            res = backtrack(alt_idx + 1, i)
            if res is not None:
                return res
            for new_i in range(i, len(text) + 1):
                res = backtrack(alt_idx, new_i)
                if res is not None:
                    return res
            return None
        return None

    return backtrack(0, text_idx)


def matches_pattern(elements, text):
    """Return True if the pattern elements match all of text."""

    def match_from(el_start, text_idx):
        if el_start == len(elements):
            return text_idx == len(text)
        elem = elements[el_start]
        print(f"  debug: el_start={el_start}, elem[0]={elem[0]}")
        if elem[0] == 'char':
            if text_idx >= len(text) or text[text_idx] != elem[1]:
                return False
            return match_from(el_start + 1, text_idx + 1)
        elif elem[0] == '?':
            if text_idx >= len(text):
                return False
            return match_from(el_start + 1, text_idx + 1)
        elif elem[0] == '*':
            # star: zero or more characters
            print(f"  star branch text_idx={text_idx}")
            if match_from(el_start + 1, text_idx):
                print("    zero match success")
                return True
            for new_text_idx in range(text_idx + 1, len(text) + 1):
                print(f"    trying new_text_idx={new_text_idx}")
                if match_from(el_start + 1, new_text_idx):
                    print("      success!")
                    return True
            print("    star fails")
            return False
        elif elem[0] == 'group':
            for alt in elem[1]:
                new_idx = _match_alt(alt, text_idx, text)
                if new_idx is not None and match_from(el_start + 1, new_idx):
                    return True
            return False
        return False

    return match_from(0, 0)


def shortest_prefix_match(pattern, text):
    try:
        elements = parse_pattern(pattern)
    except ValueError:
        raise ValueError("Invalid pattern")

    for L in range(len(text) + 1):
        if matches_pattern(elements, text[:L]):
            return L
    return -1
