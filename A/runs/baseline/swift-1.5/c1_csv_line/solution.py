def parse_csv_line(line):
    """Parse one CSV record and return its fields as a list of strings.

    A field is QUOTED when its first character is a double quote; inside a
    quoted field two consecutive double quotes are one literal double quote,
    and commas are literal. The closing quote must be followed by a comma or
    the end of the line. Any other character there, or a missing closing
    quote, raises ValueError.

    Unquoted fields are runs of zero or more non-comma characters; quotes
    inside them are ordinary literal characters. Empty runs between commas
    are empty fields; an empty line is a single empty field.
    """
    fields = []
    i = 0
    n = len(line)
    while True:
        if i < n and line[i] == '"':
            # Quoted field: skip the opening quote and read until the
            # closing quote.
            i += 1
            chars = []
            closed = False
            while i < n:
                c = line[i]
                if c == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        # A pair of quotes: one literal double quote.
                        chars.append('"')
                        i += 2
                    else:
                        # This quote closes the field.
                        closed = True
                        i += 1
                        break
                else:
                    chars.append(c)
                    i += 1
            if not closed:
                raise ValueError("unterminated quoted field")
            if i < n and line[i] != ',':
                raise ValueError(
                    "unexpected character after closing quote"
                )
            fields.append(''.join(chars))
        else:
            # Unquoted field: characters up to the next comma (none if the
            # line ends here), so this also covers empty fields.
            j = i
            while j < n and line[j] != ',':
                j += 1
            fields.append(line[i:j])
            i = j
        if i >= n:
            break
        # i points at a comma; skip it and parse the next field.
        i += 1
    return fields
