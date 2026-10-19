"""POSIX-style command line tokenizer (single line, no newlines).

tokenize(line) -> list of str, or raises ValueError on:
  - a backslash with no character after it (outside single quotes),
  - an unterminated single-quoted string,
  - an unterminated double-quoted string.

Single pass over the string: every character is examined a constant number of
times, and token pieces are collected in a list and joined once per token, so
a 200 000 character line tokenizes well within the time limit.
"""

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'
BACKSLASH = '\\'


def tokenize(line):
    if not isinstance(line, str):
        raise ValueError("tokenize() expects a string")
    if '\n' in line or '\r' in line:
        raise ValueError("tokenize() expects a single line")

    n = len(line)
    tokens = []
    i = 0

    while i < n:
        c = line[i]

        # whitespace: skip runs, never produces a token
        if c == ' ' or c == '\t':
            i += 1
            continue

        # a '#' at a token boundary (start of line, or right after whitespace
        # with no token started yet) starts a comment: discard the rest
        if c == '#':
            break

        # --- start of a token: collect adjacent segments ---
        parts = []
        while i < n:
            c = line[i]
            if c == ' ' or c == '\t':
                break

            if c == SINGLE_QUOTE:
                j = line.find(SINGLE_QUOTE, i + 1)
                if j < 0:
                    raise ValueError("unterminated ' string")
                parts.append(line[i + 1:j])
                i = j + 1

            elif c == DOUBLE_QUOTE:
                j = i + 1
                buf = []
                closed = False
                while j < n:
                    d = line[j]
                    if d == DOUBLE_QUOTE:
                        closed = True
                        break
                    if d == BACKSLASH:
                        nxt = line[j + 1] if j + 1 < n else ''
                        if nxt == DOUBLE_QUOTE or nxt == BACKSLASH:
                            buf.append(nxt)
                            j += 2
                        else:
                            # ordinary literal backslash; next char is literal too
                            buf.append(BACKSLASH)
                            j += 1
                            if j < n:
                                buf.append(line[j])
                                j += 1
                    else:
                        buf.append(d)
                        j += 1
                if not closed:
                    raise ValueError('unterminated " string')
                parts.append(''.join(buf))
                i = j + 1

            elif c == BACKSLASH:
                if i + 1 >= n:
                    raise ValueError("backslash at end of line")
                # the next character is literal, whatever it is
                parts.append(line[i + 1])
                i += 2

            else:
                # ordinary unquoted character ('#' included: a token has
                # already started here, so it is literal)
                parts.append(c)
                i += 1

        tokens.append(''.join(parts))

    return tokens


if __name__ == '__main__':
    import sys
    for _line in sys.stdin.read().split('\n'):
        try:
            print(repr(tokenize(_line)))
        except ValueError as exc:
            print('ValueError:', exc)
