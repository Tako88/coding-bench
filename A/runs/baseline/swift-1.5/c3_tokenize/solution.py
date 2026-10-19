"""POSIX-style command line tokenizer.

tokenize(line) splits a single line (never containing a newline) into a list
of token strings, following the rules in TASK.md:

- Only ' ' and '\t' are whitespace and only they separate tokens.
- A token is one or more adjacent segments (unquoted run, single-quoted
  string, double-quoted string) concatenated in order.
- '\' makes the following character literal in an unquoted run; a trailing
  backslash is an error.
- Single quotes are fully literal; double quotes honor only \" and \\.
- '#' starts a comment only when it is the first character of a token.
- ValueError is raised for a trailing backslash, an unclosed single quote,
  or an unclosed double quote.

The implementation is a single O(n) pass.
"""

_WS = ' \t'


def tokenize(line):
    """Split *line* into a list of tokens. Raises ValueError on errors."""
    n = len(line)
    i = 0
    tokens = []
    cur = []           # characters accumulated for the current token
    in_token = False   # whether the current token has started
    state = 'unquoted'  # 'unquoted', 'sq' or 'dq'; meaningful iff in_token

    while i < n:
        c = line[i]
        if not in_token:
            if c in _WS:
                i += 1
                continue
            if c == '#':
                # Comment: discard the rest of the line.
                break
            in_token = True
            state = 'unquoted'

        if state == 'unquoted':
            if c in _WS:
                # End of token; whitespace never yields an empty token.
                tokens.append(''.join(cur))
                cur = []
                in_token = False
                i += 1
            elif c == '\\':
                if i + 1 >= n:
                    raise ValueError('backslash with no character after it')
                cur.append(line[i + 1])
                i += 2
            elif c == "'":
                state = 'sq'
                i += 1
            elif c == '"':
                state = 'dq'
                i += 1
            else:
                cur.append(c)
                i += 1
        elif state == 'sq':
            if c == "'":
                state = 'unquoted'
                i += 1
            else:
                # Everything inside single quotes is literal.
                cur.append(c)
                i += 1
        else:  # state == 'dq'
            if c == '"':
                state = 'unquoted'
                i += 1
            elif c == '\\':
                if i + 1 >= n:
                    raise ValueError('backslash with no character after it')
                nxt = line[i + 1]
                if nxt == '"' or nxt == '\\':
                    cur.append(nxt)
                else:
                    # Ordinary literal backslash plus the next literal char.
                    cur.append('\\')
                    cur.append(nxt)
                i += 2
            else:
                cur.append(c)
                i += 1

    if in_token:
        if state == 'sq':
            raise ValueError('unclosed single-quoted string')
        if state == 'dq':
            raise ValueError('unclosed double-quoted string')
        tokens.append(''.join(cur))

    return tokens
