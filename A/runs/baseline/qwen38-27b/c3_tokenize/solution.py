"""Command-line tokenizer (POSIX-shell style), single pass over the line.

tokenize(line) -> list of str
"""

_WS = " \t"
_WS_PLUS_QUOTES = " \t'\""


def tokenize(line):
    """Split one line (never containing a newline) into a list of strings.

    Raises ValueError for:
      * a backslash that is the last character of the line,
      * a single-quoted string that is never closed,
      * a double-quoted string that is never closed.
    """
    n = len(line)
    tokens = []
    i = 0

    while i < n:
        # Whitespace between tokens: skipped, never produces a token.
        while i < n and line[i] in _WS:
            i += 1
        if i >= n:
            break
        # '#' as the FIRST character of a token: comment to end of line.
        if line[i] == "#":
            break

        # Build one token from its adjacent segments; 'parts' holds chunks
        # that are joined once, so no string is ever appended to repeatedly.
        parts = []
        while i < n and line[i] not in _WS:
            c = line[i]
            if c == "'":
                # Single-quoted segment: every character up to the next
                # single quote is literal (backslashes included).
                j = line.find("'", i + 1)
                if j < 0:
                    raise ValueError("unterminated single-quoted string")
                parts.append(line[i + 1:j])
                i = j + 1
            elif c == '"':
                # Double-quoted segment: only \" and \\ are escapes; any
                # other backslash (and the character after it) is literal.
                i += 1
                seg = []
                closed = False
                while i < n:
                    c = line[i]
                    if c == '"':
                        closed = True
                        i += 1
                        break
                    if c == "\\":
                        i += 1
                        if i >= n:
                            raise ValueError(
                                "backslash with no character after it")
                        d = line[i]
                        if d == '"' or d == "\\":
                            seg.append(d)
                        else:
                            seg.append("\\" + d)
                        i += 1
                    else:
                        seg.append(c)
                        i += 1
                if not closed:
                    raise ValueError("unterminated double-quoted string")
                parts.append("".join(seg))
            else:
                # Unquoted run: up to whitespace, a quote, or end of line.
                # A backslash is dropped from the token and makes the
                # character after it literal (even if that is whitespace,
                # a quote, '#' or another backslash), so the run only has
                # to re-slice around those escape points.
                seg = []
                start = i
                while i < n:
                    c = line[i]
                    if c in _WS_PLUS_QUOTES:
                        break
                    if c == "\\":
                        seg.append(line[start:i])
                        i += 1
                        if i >= n:
                            raise ValueError(
                                "backslash with no character after it")
                        seg.append(line[i])
                        i += 1
                        start = i
                    else:
                        i += 1
                seg.append(line[start:i])
                parts.extend(seg)

        tokens.append("".join(parts))

    return tokens
