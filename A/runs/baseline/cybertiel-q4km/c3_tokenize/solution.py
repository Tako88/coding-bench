"""POSIX-ish command line tokenizer.

tokenize(line) splits a single line into the list of strings a POSIX shell
would produce, following the rules in TASK.md.
"""


def tokenize(line):
    tokens = []
    i = 0
    n = len(line)
    at_start = True  # next non-whitespace char begins a new token

    while i < n:
        c = line[i]
        # Skip whitespace between tokens.
        if c == ' ' or c == '\t':
            i += 1
            at_start = True
            continue

        # A '#' at the start of a token begins a comment (rest of line discarded).
        if at_start and c == '#':
            break

        at_start = False

        # Build one token from adjacent segments.
        buf = []
        while True:
            if i >= n:
                break
            c = line[i]

            if c == "'":
                # Single-quoted string: everything literal until the next '.
                i += 1
                start = i
                while i < n and line[i] != "'":
                    i += 1
                if i >= n:
                    raise ValueError("unterminated single-quoted string")
                buf.append(line[start:i])
                i += 1  # consume closing quote

            elif c == '"':
                # Double-quoted string.
                i += 1
                closed = False
                while i < n:
                    ch = line[i]
                    if ch == '\\':
                        if i + 1 >= n:
                            raise ValueError("unterminated escape in double quotes")
                        nxt = line[i + 1]
                        if nxt == '"':
                            buf.append('"')
                        elif nxt == '\\':
                            buf.append('\\')
                        else:
                            buf.append('\\')
                            buf.append(nxt)
                        i += 2
                    elif ch == '"':
                        i += 1
                        closed = True
                        break
                    else:
                        buf.append(ch)
                        i += 1
                if not closed:
                    raise ValueError("unterminated double-quoted string")

            elif c == '\\':
                # Backslash escape in unquoted context.
                if i + 1 >= n:
                    raise ValueError("backslash with no character after it")
                buf.append(line[i + 1])
                i += 2

            elif c == ' ' or c == '\t':
                # Whitespace ends the token.
                break

            else:
                buf.append(c)
                i += 1

        tokens.append(''.join(buf))

    return tokens
