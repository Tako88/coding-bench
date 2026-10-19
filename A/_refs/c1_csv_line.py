"""Reference solution for c1_csv_line. Standalone: an explicit state machine,
written differently from the grader's reference parser."""

NONE, BARE, SINGLE, DOUBLE, AFTER = 0, 1, 2, 3, 4


def parse_csv_line(line):
    fields = []
    buf = []
    state = NONE
    i = 0
    n = len(line)

    def flush():
        fields.append("".join(buf))
        del buf[:]

    while True:
        if state == NONE:
            if i >= n:
                flush()
                return fields
            c = line[i]
            if c == ",":
                flush()
                i += 1
            elif c == '"':
                state = DOUBLE
                i += 1
            else:
                buf.append(c)
                state = BARE
                i += 1
        elif state == BARE:
            if i >= n:
                flush()
                return fields
            c = line[i]
            if c == ",":
                flush()
                state = NONE
                i += 1
            else:
                buf.append(c)
                i += 1
        elif state == SINGLE:
            if i >= n:
                raise ValueError("unterminated quoted field")
            c = line[i]
            if c == '"':
                if i + 1 < n and line[i + 1] == '"':
                    buf.append('"')
                    i += 2
                else:
                    state = AFTER
                    i += 1
            else:
                buf.append(c)
                i += 1
        elif state == DOUBLE:
            if i >= n:
                raise ValueError("unterminated quoted field")
            c = line[i]
            if c == '"':
                if i + 1 < n and line[i + 1] == '"':
                    buf.append('"')
                    i += 2
                else:
                    state = AFTER
                    i += 1
            else:
                buf.append(c)
                i += 1
        else:
            if i >= n:
                flush()
                return fields
            if line[i] != ",":
                raise ValueError("characters after closing quote")
            flush()
            state = NONE
            i += 1
