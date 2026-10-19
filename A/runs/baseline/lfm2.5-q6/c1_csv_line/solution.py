def parse_csv_line(line):
    """Parse a single CSV record and return the list of fields as strings.

    Raises ValueError for unterminated quoted fields or invalid characters
    after a quoted field's closing quote.
    """
    if line == '':
        return ['']

    fields = []
    i = 0
    n = len(line)

    while i < n:
        # Empty field from a leading comma
        if line[i] == ',':
            fields.append('')
            i += 1
            continue

        # Quoted field: starts with a double quote
        if line[i] == '"':
            i += 1  # skip opening quote
            content = []
            closing_quote_found = False

            while i < n:
                if line[i] == '"':
                    # Check for escaped double quote ("")
                    if i + 1 < n and line[i + 1] == '"':
                        content.append('"')
                        i += 2
                        # If followed by a separator comma, close the field
                        if i < n and line[i] == ',':
                            closing_quote_found = True
                            i += 1
                            break
                    else:
                        # Closing quote
                        closing_quote_found = True
                        i += 1
                        break
                else:
                    content.append(line[i])
                    i += 1

            if not closing_quote_found:
                raise ValueError("Unterminated quoted field")

            fields.append(''.join(content))
        else:
            # Unquoted field: zero or more non-comma characters
            start = i
            while i < n and line[i] != ',':
                i += 1
            fields.append(line[start:i])

        # If a quoted field was closed, handle trailing comma / remaining content
        if closing_quote_found:
            if i < n:
                # More content on the line -> parse it as the next field
                continue
            else:
                break

        if i >= n:
            break

    # If the line ends with a comma, there is an extra empty field at the end
    if line and line[-1] == ',':
        fields.append('')

    return fields
