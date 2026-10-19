# CSV record parser

Implement parse_csv_line(line) in solution.py.

Parse one CSV record and return the list of fields as strings. The input is a single line
of text and never contains a newline. The line may be empty.

FIELD GRAMMAR (complete)

  - Fields are separated by commas.
  - A field is either QUOTED or UNQUOTED.
  - A QUOTED field begins with a double quote that is the very first character of the field
    (the first character of the line, or the character straight after a comma), and ends at
    a double quote that closes it. Read the field left to right from that opening quote: at
    each double quote, if the next character is also a double quote then the pair is one
    literal double quote and the field continues, otherwise this quote closes the field.
    So four double quotes in a row are one field holding one double quote. A comma inside a
    quoted field is a literal character, not a separator. A quoted field may be empty ("").
  - An UNQUOTED field is a run of zero or more characters that are not commas. A double
    quote inside an unquoted field is an ordinary literal character: it does not start a
    quoted field, because the field did not begin with it.
  - The closing quote of a quoted field must be followed by a comma or by the end of the
    line. Any other character there is an error.
  - Zero characters between two commas, before the first comma, or after the last comma is
    an EMPTY FIELD, not a missing field.
  - An empty input line is a single empty field.

ERRORS: raise ValueError for

  - a quoted field whose closing quote is missing (unterminated), or
  - any character between a quoted field's closing quote and the next comma or the end of
    the line.

EXAMPLES (every rule above appears here)

  The input column shows the characters of the line; the expected value is a Python list
  literal.

  a,b,c                -> ['a', 'b', 'c']
  a                    -> ['a']
  a,,b                 -> ['a', '', 'b']
  ,,,                  -> ['', '', '', '']
  ""                   -> ['']
  a,"b"                -> ['a', 'b']
  ,"a"                 -> ['', 'a']
  "a",                 -> ['a', '']
  "a,b",c              -> ['a,b', 'c']
  "a b"                -> ['a b']
  ","                  -> [',']
  "he said ""hi""",x   -> ['he said "hi"', 'x']
  """"                 -> ['"']
  a"b                  -> ['a"b']
  a"b"                 -> ['a"b"']
  (empty line)         -> ['']

  "unterminated        -> ValueError
  "a"x                 -> ValueError
  "a""                 -> ValueError
