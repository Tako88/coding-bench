def tokenize(line):
    tokens = []
    i = 0
    n = len(line)

    while True:
        # Skip leading whitespace
        while i < n and line[i] in ' \t':
            i += 1

        if i >= n:
            break

        # A '#' at the start of a token (after whitespace) starts a comment,
        # which discards the rest of the line.
        if line[i] == '#':
            break

        current = []

        # Parse a token: one or more segments (adjacent, no whitespace between)
        while True:
            if i >= n:
                break

            ch = line[i]

            if ch == "'":
                # Single-quoted string
                i += 1
                while True:
                    if i >= n or line[i] == "'":
                        break
                    c = line[i]
                    if c == '\\':
                        current.append(c)
                        i += 2
                        continue
                    current.append(c)
                    i += 1
                if i >= n:
                    raise ValueError("Unclosed single quote")
                tokens.append(''.join(current))
                continue

            if ch == '"':
                # Double-quoted string
                i += 1
                while True:
                    if i >= n or line[i] == '"':
                        break
                    c = line[i]
                    if c == '\\':
                        nxt = line[i + 1]
                        if nxt == '"':
                            current.append('"')
                        elif nxt == '\\':
                            current.append('\\')
                        else:
                            current.append(c)
                            current.append(nxt)
                        i += 2
                        continue
                    current.append(c)
                    i += 1
                if i >= n:
                    raise ValueError("Unclosed double quote")
                tokens.append(''.join(current))
                continue

            # Unquoted run: everything up to whitespace or end of line
            start = i
            while i < n and line[i] not in ' \t':
                c = line[i]
                if c == '\\':
                    if i + 1 >= n:
                        raise ValueError("Backslash with no character after it")
                    current.append(line[i + 1])
                    i += 2
                    continue
                current.append(c)
                i += 1
            tokens.append(''.join(current))
            # i is now at whitespace or end of line; outer loop will skip whitespace

        # Skip whitespace before the next token
        while i < n and line[i] in ' \t':
            i += 1

    return tokens
