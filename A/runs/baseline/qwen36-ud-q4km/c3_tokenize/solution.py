def tokenize(line):
    """Split a command line into tokens the way a POSIX shell does."""
    tokens = []
    i = 0
    n = len(line)

    while i < n:
        # Skip whitespace (space and tab only)
        while i < n and line[i] in (' ', '\t'):
            i += 1
        if i >= n:
            break

        # Check for comment at start of token
        if line[i] == '#':
            break

        # Parse adjacent segments into one token
        token_parts = []

        while i < n:
            c = line[i]

            if c == "'":
                # Single-quoted string: everything between '...' is literal
                i += 1
                part = []
                while i < n and line[i] != "'":
                    part.append(line[i])
                    i += 1
                if i >= n:
                    raise ValueError("unclosed single quote")
                i += 1  # skip closing '
                token_parts.append(''.join(part))

            elif c == '"':
                # Double-quoted string
                i += 1
                part = []
                found_close = False
                while i < n:
                    c2 = line[i]
                    if c2 == '"':
                        i += 1
                        found_close = True
                        break
                    elif c2 == '\\':
                        i += 1
                        if i >= n:
                            raise ValueError("trailing backslash")
                        c3 = line[i]
                        if c3 == '"':
                            part.append('"')
                        elif c3 == '\\':
                            part.append('\\')
                        else:
                            part.append('\\')
                            part.append(c3)
                        i += 1
                    else:
                        part.append(c2)
                        i += 1
                if not found_close:
                    raise ValueError("unclosed double quote")
                token_parts.append(''.join(part))

            elif c == '\\':
                # Unquoted backslash escape: next char is literal
                i += 1
                if i >= n:
                    raise ValueError("trailing backslash")
                token_parts.append(line[i])
                i += 1

            else:
                # Unquoted run: collect until whitespace, quote, or backslash
                part = []
                while i < n and line[i] not in (' ', '\t', "'", '"', '\\'):
                    part.append(line[i])
                    i += 1
                token_parts.append(''.join(part))

            # After a segment, stop if whitespace or end of line
            if i >= n or line[i] in (' ', '\t'):
                break

        tokens.append(''.join(token_parts))

    return tokens
