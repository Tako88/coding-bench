"""CSV record parser."""


def parse_csv_line(line):
    """Parse a single CSV record and return the list of fields as strings."""
    fields = []
    i = 0
    n = len(line)
    while True:
        if i < n and line[i] == '"':
            # Quoted field.
            i += 1  # skip opening quote
            buf = []
            closed = False
            while i < n:
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        # Escaped double quote: one literal quote, keep going.
                        buf.append('"')
                        i += 2
                    else:
                        # Closing quote.
                        closed = True
                        i += 1
                        break
                else:
                    buf.append(line[i])
                    i += 1
            if not closed:
                raise ValueError("unterminated quoted field")
            value = ''.join(buf)
            if i < n and line[i] != ',':
                raise ValueError("unexpected character after closing quote")
        else:
            # Unquoted field: run of characters up to the next comma.
            j = i
            while j < n and line[j] != ',':
                j += 1
            value = line[i:j]
            i = j
        fields.append(value)
        if i >= n:
            break
        # line[i] == ',' -> start next field
        i += 1
    return fields
