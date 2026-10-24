"""CSV record parser (standard library only)."""


def parse_csv_line(line):
    """Parse a single CSV record (no embedded newline) into a list of field strings."""
    fields = []
    i = 0
    n = len(line)

    while True:
        if i < n and line[i] == '"':
            # QUOTED field
            i += 1
            buf = []
            while True:
                if i >= n:
                    raise ValueError("unterminated quoted field")
                c = line[i]
                if c == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        buf.append('"')
                        i += 2
                    else:
                        i += 1  # closing quote
                        break
                else:
                    buf.append(c)
                    i += 1
            # closing quote must be followed by comma or end of line
            if i < n and line[i] != ',':
                raise ValueError("character after closing quote of quoted field")
            fields.append(''.join(buf))
        else:
            # UNQUOTED field: run of characters that are not commas
            buf = []
            while i < n and line[i] != ',':
                buf.append(line[i])
                i += 1
            fields.append(''.join(buf))

        if i < n and line[i] == ',':
            i += 1
            continue
        break

    return fields
