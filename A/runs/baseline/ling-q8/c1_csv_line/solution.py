def parse_csv_line(line):
    """Parse a single CSV line and return the list of fields as strings."""
    fields = []
    i = 0
    n = len(line)

    while i <= n:
        # After a comma (or at start of line), parse a field
        if i == n:
            # End of line
            break

        if line[i] == ',':
            # Empty field
            fields.append('')
            i += 1
            continue

        # Parse a field
        # Check if it starts with a quote
        if line[i] == '"':
            # Quoted field
            i += 1  # skip opening quote
            field_chars = []
            while i < n:
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        # Escaped quote
                        field_chars.append('"')
                        i += 2
                    else:
                        # Closing quote
                        break
                else:
                    field_chars.append(line[i])
                    i += 1

            # After parsing the quoted field, check that we're at a comma or end of line
            if i >= n:
                raise ValueError("unterminated quoted field")
            if line[i] != ',':
                raise ValueError("closing quote not followed by comma or end of line")
            fields.append(''.join(field_chars))
            i += 1
        else:
            # Unquoted field: read until comma or end of line
            field_chars = []
            while i < n and line[i] != ',':
                field_chars.append(line[i])
                i += 1
            fields.append(''.join(field_chars))

    return fields
