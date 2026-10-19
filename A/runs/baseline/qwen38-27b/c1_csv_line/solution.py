def parse_csv_line(line):
    """Parse one CSV record and return the list of fields as strings.

    Raises ValueError for an unterminated quoted field or for any
    character between a quoted field's closing quote and the next
    comma or end of line.
    """
    if line == '':
        return ['']
    n = len(line)
    fields = []
    i = 0
    while i < n:
        if line[i] == '"':
            # QUOTED field: opening quote is the first character of the field.
            i += 1
            buf = []
            closed = False
            while i < n:
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        # pair of quotes = one literal double quote
                        buf.append('"')
                        i += 2
                    else:
                        # closing quote
                        closed = True
                        i += 1
                        break
                else:
                    buf.append(line[i])
                    i += 1
            if not closed:
                raise ValueError('unterminated quoted field')
            # Closing quote must be followed by a comma or end of line.
            if i < n and line[i] != ',':
                raise ValueError('unexpected character after closing quote')
            value = ''.join(buf)
        else:
            # UNQUOTED field: run of non-comma characters.
            buf = []
            while i < n and line[i] != ',':
                buf.append(line[i])
                i += 1
            value = ''.join(buf)
        fields.append(value)
        if i < n:
            i += 1  # skip the comma separator
            if i == n:
                # Line ends with a comma: final empty field.
                fields.append('')
                break
    return fields
