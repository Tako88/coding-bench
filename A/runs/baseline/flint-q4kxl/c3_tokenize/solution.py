"""Command line tokenizer."""


def tokenize(line):
    tokens = []
    cur = []
    token_started = False
    state = 0  # 0 = normal, 1 = single-quoted, 2 = double-quoted
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if state == 0:
            if ch == ' ' or ch == '\t':
                if token_started:
                    tokens.append(''.join(cur))
                    del cur[:]
                    token_started = False
                i += 1
            elif ch == '#':
                if not token_started:
                    # comment: discard the rest of the line
                    break
                cur.append(ch)
                token_started = True
                i += 1
            elif ch == "'":
                state = 1
                token_started = True
                i += 1
            elif ch == '"':
                state = 2
                token_started = True
                i += 1
            elif ch == '\\':
                if i + 1 >= n:
                    raise ValueError("dangling backslash")
                cur.append(line[i + 1])
                token_started = True
                i += 2
            else:
                cur.append(ch)
                token_started = True
                i += 1
        elif state == 1:
            if ch == "'":
                state = 0
                i += 1
            else:
                cur.append(ch)
                i += 1
        else:  # state == 2
            if ch == '\\':
                if i + 1 >= n:
                    raise ValueError("dangling backslash")
                nxt = line[i + 1]
                if nxt == '"':
                    cur.append('"')
                    i += 2
                elif nxt == '\\':
                    cur.append('\\')
                    i += 2
                else:
                    cur.append('\\')
                    cur.append(nxt)
                    i += 2
            elif ch == '"':
                state = 0
                i += 1
            else:
                cur.append(ch)
                i += 1
    if state != 0:
        raise ValueError("unterminated quote")
    if token_started:
        tokens.append(''.join(cur))
    return tokens
