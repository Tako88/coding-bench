"""Single-pass POSIX-style command line tokenizer (standard library only)."""


def tokenize(line):
    """Split one command line into a list of strings, the way a POSIX shell does.

    Raises ValueError for a trailing backslash, an unclosed single-quoted
    string, or an unclosed double-quoted string.
    """
    n = len(line)
    i = 0
    tokens = []
    buf = []          # characters accumulated for the current token
    in_token = False  # True once a token has started (first segment seen)

    while i < n:
        c = line[i]

        # Whitespace separates tokens; never produces an empty token.
        if c == ' ' or c == '\t':
            if in_token:
                tokens.append(''.join(buf))
                buf = []
                in_token = False
            i += 1
            continue

        # A '#' starts a comment only as the first character of a token.
        if c == '#' and not in_token:
            break

        # Backslash in an unquoted run: next character becomes literal.
        if c == '\\':
            if i + 1 >= n:
                raise ValueError('a backslash with no character after it')
            buf.append(line[i + 1])
            in_token = True
            i += 2
            continue

        # Single-quoted string: everything up to the next ' is literal.
        if c == "'":
            j = line.find("'", i + 1)
            if j < 0:
                raise ValueError('a single-quoted string that is never closed')
            if j > i + 1:
                buf.append(line[i + 1:j])
            in_token = True
            i = j + 1
            continue

        # Double-quoted string: ends at the next unescaped ".
        if c == '"':
            j = i + 1
            parts = []
            while j < n:
                d = line[j]
                if d == '"':
                    break
                if d == '\\':
                    if j + 1 < n:
                        e = line[j + 1]
                        if e == '"' or e == '\\':
                            parts.append(e)
                        else:
                            # Any other backslash stays literal, and so does
                            # the character after it.
                            parts.append(d)
                            parts.append(e)
                        j += 2
                        continue
                    # Backslash at the very end of the line inside double
                    # quotes: keep it literal; the string will turn out to
                    # be never closed.
                    parts.append(d)
                else:
                    parts.append(d)
                j += 1
            if j >= n:
                raise ValueError('a double-quoted string that is never closed')
            if parts:
                buf.append(''.join(parts))
            in_token = True
            i = j + 1
            continue

        # Ordinary literal character in an unquoted run.
        buf.append(c)
        in_token = True
        i += 1

    if in_token:
        tokens.append(''.join(buf))
    return tokens
