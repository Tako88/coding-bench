"""CSV record parser.

Implements parse_csv_line(line) per the task grammar:

  - Fields are separated by commas.
  - A field is QUOTED if its first character is a double quote, otherwise UNQUOTED.
  - QUOTED fields: read from the opening quote; a "" pair is one literal quote and the
    field continues; any other quote closes the field.  A comma inside a quoted field is
    literal.  The closing quote must be followed by a comma or end of line.
  - UNQUOTED fields: a run of zero or more characters that are not commas; double quotes
    inside them are ordinary literal characters.
  - Zero characters between commas / before the first comma / after the last comma is an
    empty field.  An empty line is a single empty field.

Raises ValueError for an unterminated quoted field or for stray characters after a quoted
field's closing quote.
"""


def parse_csv_line(line):
    """Parse one CSV record and return the list of fields as strings."""
    if not isinstance(line, str):
        raise ValueError("input must be a single line of text")

    n = len(line)
    fields = []
    i = 0

    while True:
        if i < n and line[i] == '"':
            # ---- QUOTED field ----
            i += 1  # consume the opening quote
            chars = []
            closed = False
            while i < n:
                ch = line[i]
                if ch == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        # A doubled quote is one literal quote; field continues.
                        chars.append('"')
                        i += 2
                        continue
                    # This quote closes the field.
                    i += 1
                    closed = True
                    break
                chars.append(ch)
                i += 1

            if not closed:
                raise ValueError("unterminated quoted field")

            # The closing quote must be followed by a comma or the end of the line.
            if i < n and line[i] != ',':
                raise ValueError(
                    "unexpected character after closing quote: %r" % (line[i],)
                )

            fields.append("".join(chars))
        else:
            # ---- UNQUOTED field: everything up to the next comma (may be empty) ----
            j = i
            while j < n and line[j] != ',':
                j += 1
            fields.append(line[i:j])
            i = j

        # i is either at end of line or at a comma separator here.
        if i < n:
            # Consume the separator: there is always another field after a comma.
            i += 1
            continue
        return fields
