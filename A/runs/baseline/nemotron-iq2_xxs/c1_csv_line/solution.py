def parse_csv_line(line):
    """Parse a single CSV record (no newlines) into a list of fields.

    Field grammar (from TASK.md):
      - Fields are separated by commas.
      - A QUOTED field starts with a double quote as the first character of
        the field and ends at a closing double quote. Inside a quoted field,
        two consecutive double quotes are one literal double quote and the
        field continues. A comma inside a quoted field is literal.
      - An UNQUOTED field is a run of characters that are not commas; a
        double quote inside it is an ordinary literal.
      - The closing quote of a quoted field must be followed by a comma or
        the end of the line; anything else is an error.
      - Zero characters between commas (or at the ends) is an empty field.
      - An empty input line is a single empty field.

    Raises ValueError for an unterminated quoted field or for any character
    between a closing quote and the next comma/end of line.
    """
    fields = []
    current = []
    in_quotes = False
    i = 0
    n = len(line)

    while i < n:
        if in_quotes:
            c = line[i]
            if c == '"':
                if i + 1 < n and line[i + 1] == '"':
                    # Escaped quote: one literal double quote, continue.
                    current.append('"')
                    i += 2
                else:
                    # Closing quote.
                    in_quotes = False
                    i += 1
                    if i < n and line[i] != ',':
                        raise ValueError(
                            'expected comma or end of line after closing quote'
                        )
                    continue
            else:
                current.append(c)
                i += 1
        else:
            c = line[i]
            if c == '"' and not current:
                # A double quote only starts a quoted field if it is the
                # very first character of the field. Otherwise it is a
                # literal character inside an unquoted field.
                in_quotes = True
                i += 1
            elif c == ',':
                fields.append(''.join(current))
                current = []
                i += 1
            else:
                current.append(c)
                i += 1

    if in_quotes:
        raise ValueError('unterminated quoted field')

    fields.append(''.join(current))
    return fields
