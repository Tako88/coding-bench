def tokenize(line):
    """Split a single command line into tokens the way a POSIX shell does.

    Returns a list of strings. Raises ValueError on malformed input.
    """
    tokens = []
    i = 0
    n = len(line)

    while i < n:
        c = line[i]
        # Skip whitespace separators.
        if c == ' ' or c == '\t':
            i += 1
            continue

        # Start of a token. Build it from adjacent segments.
        parts = []
        first = True
        while i < n:
            c = line[i]
            # Whitespace ends the token.
            if c == ' ' or c == '\t':
                break
            # Quoted segments.
            if c == "'" or c == '"':
                quote = c
                double = (c == '"')
                i += 1
                buf = []
                closed = False
                while i < n:
                    cc = line[i]
                    if cc == quote:
                        i += 1
                        closed = True
                        break
                    if double and cc == '\\':
                        i += 1
                        if i >= n:
                            raise ValueError("unterminated quoted string")
                        nxt = line[i]
                        if nxt == '"':
                            buf.append('"')
                        elif nxt == '\\':
                            buf.append('\\')
                        else:
                            buf.append('\\')
                            buf.append(nxt)
                        i += 1
                        continue
                    buf.append(cc)
                    i += 1
                if not closed:
                    raise ValueError("unterminated quoted string")
                parts.append(''.join(buf))
                first = False
                continue
            # Backslash escapes.
            if c == '\\':
                i += 1
                if i >= n:
                    raise ValueError("trailing backslash")
                parts.append(line[i])
                i += 1
                first = False
                continue
            # Comment: '#' only at the very first character of a token.
            if c == '#' and first:
                return tokens
            parts.append(c)
            first = False
            i += 1

        if parts:
            tokens.append(''.join(parts))

    return tokens
