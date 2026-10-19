"""CSV record parser.

parse_csv_line(line) parses one CSV record (a single line of text, never
containing a newline) and returns the list of fields as strings.

Grammar (complete):
  - Fields are separated by commas.
  - A field is either QUOTED or UNQUOTED.
  - A QUOTED field begins with a double quote that is the very first
    character of the field (first character of the line, or the character
    straight after a comma), and ends at a closing double quote. Reading
    left to right from the opening quote: at each double quote, if the next
    character is also a double quote the pair is one literal double quote
    and the field continues; otherwise this quote closes the field.
    A comma inside a quoted field is a literal character, not a separator.
    A quoted field may be empty ("").
  - An UNQUOTED field is a run of zero or more characters that are not
    commas. A double quote inside an unquoted field is an ordinary literal
    character.
  - The closing quote of a quoted field must be followed by a comma or the
    end of the line; any other character there is an error.
  - Zero characters between two commas, before the first comma, or after
    the last comma is an EMPTY FIELD, not a missing field.
  - An empty input line is a single empty field.

Errors (ValueError):
  - a quoted field whose closing quote is missing (unterminated), or
  - any character between a quoted field's closing quote and the next comma
    or the end of the line.
"""


def parse_csv_line(line):
    """Parse one CSV record and return the list of fields as strings.

    Raises ValueError for an unterminated quoted field or for any character
    between a quoted field's closing quote and the next comma or the end of
    the line.
    """
    fields = []
    i = 0
    n = len(line)
    while True:
        if i < n and line[i] == '"':
            # QUOTED field: line[i] is the opening quote.
            i += 1  # consume the opening quote
            buf = []
            while True:
                if i >= n:
                    raise ValueError(
                        "unterminated quoted field: missing closing quote"
                    )
                c = line[i]
                if c == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        # Pair of double quotes: one literal double quote.
                        buf.append('"')
                        i += 2
                    else:
                        # This quote closes the field.
                        i += 1
                        break
                else:
                    # Any other character (including a comma) is literal.
                    buf.append(c)
                    i += 1
            # After the closing quote must be a comma or the end of the line.
            if i < n and line[i] != ',':
                raise ValueError(
                    "unexpected character %r after closing quote" % line[i]
                )
            fields.append(''.join(buf))
        else:
            # UNQUOTED field: a run of zero or more non-comma characters.
            j = i
            while j < n and line[j] != ',':
                j += 1
            fields.append(line[i:j])
            i = j
        # Move past the separator comma, if any; otherwise the line is done.
        if i < n:  # line[i] is necessarily ','
            i += 1
        else:
            break
    return fields
