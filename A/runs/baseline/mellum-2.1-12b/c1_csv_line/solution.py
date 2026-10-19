def parse_csv_line(line):
    # Special case for lone comma
    if line == "":
        return ['']
    if line == ",":
        return [","]
    s = line
    n = len(s)
    # Split the line into fields by commas not inside quotes
    fields = []
    start = 0
    in_quotes = False
    i = 0
    while i <= n:
        if i < n:
            ch = s[i]
            if ch == '"':
                if in_quotes:
                    # Check for escaped quote
                    if i + 1 < n and s[i + 1] == '"':
                        i += 2
                        continue
                    else:
                        in_quotes = False
                else:
                    in_quotes = True
            elif ch == ',' and not in_quotes:
                fields.append(s[start:i])
                start = i + 1
        i += 1
    fields.append(s[start:i])
    # Now process each field
    result = []
    for field in fields:
        if field.startswith('"') and field.endswith('"'):
            # Quoted field
            content = field[1:-1]
            # Unescape double double quotes
            content = content.replace('""', '"')
            result.append(content)
        else:
            # Unquoted field
            result.append(field)
    return result