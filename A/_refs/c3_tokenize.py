"""Reference solution for c3_tokenize. Standalone explicit state machine."""

NONE, BARE, SINGLE, DOUBLE = 0, 1, 2, 3


def tokenize(line):
    out = []
    buf = []
    state = NONE
    i = 0
    n = len(line)

    def flush():
        out.append("".join(buf))
        del buf[:]

    while i < n:
        c = line[i]
        if state == NONE:
            if c == " " or c == "\t":
                i += 1
            elif c == "#":
                i = n
            elif c == "\\":
                if i + 1 >= n:
                    raise ValueError("backslash with no character after it")
                buf.append(line[i + 1])
                state = BARE
                i += 2
            elif c == "'":
                state = SINGLE
                i += 1
            elif c == '"':
                state = DOUBLE
                i += 1
            else:
                buf.append(c)
                state = BARE
                i += 1
        elif state == BARE:
            if c == " " or c == "\t":
                flush()
                state = NONE
                i += 1
            elif c == "\\":
                if i + 1 >= n:
                    raise ValueError("backslash with no character after it")
                buf.append(line[i + 1])
                i += 2
            elif c == "'":
                state = SINGLE
                i += 1
            elif c == '"':
                state = DOUBLE
                i += 1
            else:
                buf.append(c)
                i += 1
        elif state == SINGLE:
            if c == "'":
                state = BARE
            else:
                buf.append(c)
            i += 1
        else:
            if c == '"':
                state = BARE
                i += 1
            elif c == "\\" and i + 1 < n and line[i + 1] in '"\\':
                buf.append(line[i + 1])
                i += 2
            elif c == "\\":
                buf.append("\\")
                i += 1
            else:
                buf.append(c)
                i += 1
    if state == SINGLE or state == DOUBLE:
        raise ValueError("unterminated quoted string")
    if state == BARE:
        flush()
    return out
