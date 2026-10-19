def parse_csv_line(line):
    """Parse a single CSV record and return the list of fields as strings.

    Raises ValueError for an unterminated quoted field or any character
    following a quoted field's closing quote.
    """
    fields = []
    i = 0
    n = len(line)

    while True:
        if i < n and line[i] == '"':
            # Quoted field.
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
            # After the closing quote there must be a comma or end of line.
            if i < n and line[i] != ',':
                raise ValueError("character after closing quote")
            fields.append(''.join(buf))
        else:
            # Unquoted field: run of characters that are not commas.
            start = i
            while i < n and line[i] != ',':
                i += 1
            fields.append(line[start:i])

        # Now at a comma or end of line.
        if i < n and line[i] == ',':
            i += 1
            if i == n:
                # Trailing comma -> final empty field.
                fields.append('')
                break
            continue
        else:
            break

    return fields
