def tokenize(line):
    """Split a single command line into tokens, like a POSIX shell.

    Whitespace is only space ' ' and tab '\t'.  A token is one or more
    adjacent segments (unquoted run, single-quoted string, double-quoted
    string) concatenated together.  Returns a list of strings; a line with
    no tokens yields [].  Raises ValueError on unterminated quotes or a
    trailing backslash.
    """
    tokens = []
    cur = None          # list of chars of the current token, None between tokens
    i = 0
    n = len(line)
    WS = (' ', '\t')

    while i < n:
        if cur is None:
            # Between tokens: skip whitespace.
            while i < n and line[i] in WS:
                i += 1
            if i >= n:
                break
            if line[i] == '#':
                # Comment: discard the rest of the line.
                break
            cur = []

        c = line[i]
        if c == '"':
            # Double-quoted segment.
            i += 1
            closed = False
            while i < n:
                c = line[i]
                if c == '\\':
                    i += 1
                    if i >= n:
                        raise ValueError("backslash with no character after it")
                    nxt = line[i]
                    if nxt == '"':
                        cur.append('"')
                    elif nxt == '\\':
                        cur.append('\\')
                    else:
                        cur.append('\\')
                        cur.append(nxt)
                    i += 1
                elif c == '"':
                    i += 1
                    closed = True
                    break
                else:
                    cur.append(c)
                    i += 1
            if not closed:
                raise ValueError("double-quoted string never closed")
        elif c == "'":
            # Single-quoted segment: everything literal.
            i += 1
            while i < n and line[i] != "'":
                cur.append(line[i])
                i += 1
            if i >= n:
                raise ValueError("single-quoted string never closed")
            i += 1  # skip closing quote
        else:
            # Unquoted run.
            while i < n:
                c = line[i]
                if c in WS or c == '"' or c == "'":
                    break
                if c == '\\':
                    i += 1
                    if i >= n:
                        raise ValueError("backslash with no character after it")
                    cur.append(line[i])
                    i += 1
                else:
                    cur.append(c)
                    i += 1

        # End the token when whitespace or end of line follows the segment.
        if cur is not None and (i >= n or line[i] in WS):
            tokens.append(''.join(cur))
            cur = None

    if cur is not None:
        tokens.append(''.join(cur))
    return tokens
