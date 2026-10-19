def tokenize(line):
    """Tokenize a command line the way a POSIX shell does."""
    result = []
    i = 0
    n = len(line)

    while i < n:
        # Skip whitespace
        while i < n and line[i] in (' ', '\t'):
            i += 1
        if i >= n:
            break

        # Check for comment: '#' is first char of a token
        if line[i] == '#':
            break  # skip rest of line

        # Build a token from adjacent segments
        token_segments = []
        while i < n and line[i] not in (' ', '\t'):
            if line[i] == "'":
                # Single-quoted segment: everything until next '
                i += 1  # skip opening '
                seg_chars = []
                while i < n and line[i] != "'":
                    seg_chars.append(line[i])
                    i += 1
                if i >= n:
                    raise ValueError("Unclosed single-quoted string")
                i += 1  # skip closing '
                token_segments.append(''.join(seg_chars))

            elif line[i] == '"':
                # Double-quoted segment
                i += 1  # skip opening "
                seg_chars = []
                closed = False
                while i < n:
                    ch = line[i]
                    if ch == '"':
                        i += 1
                        closed = True
                        break
                    elif ch == '\\':
                        if i + 1 >= n:
                            raise ValueError("Backslash at end of line")
                        nxt = line[i + 1]
                        if nxt == '"':
                            seg_chars.append('"')
                        elif nxt == '\\':
                            seg_chars.append('\\')
                        else:
                            seg_chars.append('\\')
                            seg_chars.append(nxt)
                        i += 2
                    else:
                        seg_chars.append(ch)
                        i += 1
                if not closed:
                    raise ValueError("Unclosed double-quoted string")
                token_segments.append(''.join(seg_chars))

            else:
                # Unquoted run: until whitespace, quote, or end
                seg_chars = []
                while i < n and line[i] not in (' ', '\t', "'", '"'):
                    if line[i] == '\\':
                        if i + 1 >= n:
                            raise ValueError("Backslash at end of line")
                        seg_chars.append(line[i + 1])
                        i += 2
                    else:
                        seg_chars.append(line[i])
                        i += 1
                token_segments.append(''.join(seg_chars))

        result.append(''.join(token_segments))

    return result
