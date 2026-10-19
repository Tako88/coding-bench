def parse_csv_line(line):
    """Parse a single CSV line and return a list of field strings."""
    fields = []
    i = 0
    n = len(line)
    more = True  # whether there might be more fields after a comma

    while more:
        more = False
        if i >= n:
            fields.append('')
            break

        if line[i] == '"':
            # Quoted field
            i += 1  # skip opening quote
            field_chars = []
            while i < n:
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        # Escaped double quote
                        field_chars.append('"')
                        i += 2
                    else:
                        # Closing quote
                        i += 1
                        if i < n and line[i] != ',':
                            raise ValueError(
                                "Character after closing quote of quoted field"
                            )
                        if i < n:
                            i += 1  # skip comma
                            more = True
                        fields.append(''.join(field_chars))
                        break
                else:
                    field_chars.append(line[i])
                    i += 1
            else:
                # while loop exited without break → unterminated
                raise ValueError("Unterminated quoted field")
        else:
            # Unquoted field
            field_chars = []
            while i < n and line[i] != ',':
                field_chars.append(line[i])
                i += 1
            if i < n and line[i] == ',':
                i += 1
                more = True
            fields.append(''.join(field_chars))

    return fields
