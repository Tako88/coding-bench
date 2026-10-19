def tokenize(line):
    tokens = []
    current = None  # list of chars for current token, or None if not in token
    i = 0
    n = len(line)

    def add_token():
        nonlocal current
        if current is not None:
            tokens.append(''.join(current))
            current = None

    while i < n:
        # Check for whitespace
        if line[i] == ' ' or line[i] == '\t':
            add_token()
            i += 1
            continue

        # Check for comment start at token beginning
        if current is None and line[i] == '#':
            return tokens

        # Parse a segment
        if line[i] == "'":
            # single-quoted string
            i += 1
            seg_chars = []
            while i < n:
                if line[i] == "'":
                    i += 1
                    break
                elif line[i] == '\\':
                    i += 1
                    if i < n:
                        seg_chars.append('\\')
                        seg_chars.append(line[i])
                        i += 1
                    else:
                        raise ValueError("backslash with no character after it")
                else:
                    seg_chars.append(line[i])
                    i += 1
            else:
                raise ValueError("single-quoted string not closed")
            segment = ''.join(seg_chars)
        elif line[i] == '"':
            # double-quoted string
            i += 1
            seg_chars = []
            while i < n:
                if line[i] == '"':
                    i += 1
                    break
                elif line[i] == '\\':
                    i += 1
                    if i < n:
                        c = line[i]
                        if c == '"':
                            seg_chars.append('"')
                        elif c == '\\':
                            seg_chars.append('\\')
                        else:
                            seg_chars.append('\\')
                            seg_chars.append(c)
                        i += 1
                    else:
                        raise ValueError("backslash with no character after it")
                else:
                    seg_chars.append(line[i])
                    i += 1
            else:
                raise ValueError("double-quoted string not closed")
            segment = ''.join(seg_chars)
        else:
            # unquoted run
            seg_chars = []
            while i < n and line[i] not in ' \t':
                if line[i] == '\\':
                    i += 1
                    if i < n:
                        seg_chars.append(line[i])
                        i += 1
                    else:
                        raise ValueError("backslash with no character after it")
                else:
                    seg_chars.append(line[i])
                    i += 1
            segment = ''.join(seg_chars)

        # We have a segment
        if current is None:
            current = []
        current.extend(segment)

    add_token()
    return tokens
