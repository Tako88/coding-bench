def parse_csv_line(line):
    """Parse a single CSV line and return a list of field strings."""
    if line == "":
        return [""]

    fields = []
    i = 0
    n = len(line)

    while True:
        if i >= n:
            # We've consumed everything; if we're here with no field collected yet
            # (trailing comma case), add empty field
            fields.append("")
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
                        i += 1  # skip closing quote
                        # Next character must be comma or end of line
                        if i < n and line[i] != ',':
                            raise ValueError(
                                f"Character after closing quote is invalid: {line[i]}"
                            )
                        break
                else:
                    field_chars.append(line[i])
                    i += 1
            else:
                # Reached end of line without closing quote
                raise ValueError("Unterminated quoted field")

            fields.append("".join(field_chars))

            if i < n and line[i] == ',':
                i += 1  # skip comma, continue to next field
                continue
            else:
                # End of line
                break
        else:
            # Unquoted field
            start = i
            while i < n and line[i] != ',':
                i += 1
            fields.append(line[start:i])

            if i < n and line[i] == ',':
                i += 1  # skip comma, continue to next field
                continue
            else:
                # End of line
                break

    return fields
