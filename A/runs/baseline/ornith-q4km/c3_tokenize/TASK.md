# command line tokenizer

Implement tokenize(line) in solution.py.

Split one command line into a list of strings, the way a POSIX shell does. The input is a
single line and never contains a newline.

TOKENS AND SEGMENTS

  - Whitespace separates tokens. The only whitespace characters are the space ' ' and the
    tab '\t'.
  - A token is built from one or more SEGMENTS that are adjacent, meaning there is no
    whitespace between them. Adjacent segments are concatenated into a single token, in
    the order they appear.
  - The three kinds of segment are: an unquoted run, a single-quoted string, and a
    double-quoted string.
  - A segment may be empty. '' and "" are empty segments that still make their token
    exist, so a token can be the empty string.
  - Leading and trailing whitespace is ignored, and a run of whitespace never produces an
    empty token.

UNQUOTED RUN

  - An unquoted run is everything up to the next whitespace, up to the next quote, or up
    to the end of the line.
  - A backslash '\' makes the character after it literal: that character is added to the
    token as-is, and it may be whitespace, a quote, a '#' or another backslash. A
    backslash with no character after it (it is the last character of the line) is an
    error.
  - An escaped whitespace character does NOT separate tokens.

SINGLE QUOTES

  - A single-quoted string starts at ' and ends at the next '. Every character between
    them is literal, including backslashes and '#'.
  - A ' that is never closed is an error. There is no way to put a ' inside a
    single-quoted string.

DOUBLE QUOTES

  - A double-quoted string starts at " and ends at the next unescaped ".
  - Inside it exactly two backslash sequences are escapes: \" is one literal " and \\ is
    one literal backslash.
  - Any other backslash inside double quotes is an ordinary literal backslash, and the
    character after it is also literal: "a\qb" holds the four characters a, \, q, b.
  - A " that is never closed is an error.

COMMENTS

  - A '#' starts a comment only when it is the FIRST character of a token, meaning it is
    at the start of the line or directly after whitespace. The '#' and everything after it
    to the end of the line are discarded.
  - Everywhere else '#' is an ordinary literal character, including in the middle of a
    token and inside quoted strings.
  - A '#' that was made literal by a backslash is literal, and the token has already
    started at that backslash, so it does not start a comment.

ERRORS: raise ValueError for

  - a backslash with no character after it,
  - a single-quoted string that is never closed,
  - a double-quoted string that is never closed.

RETURN: a list of strings. A line with no tokens at all (empty, whitespace only, or a
comment only) gives [].

PERFORMANCE: the line may be 200,000 characters long and the call must finish within
3 seconds. Repeatedly appending to a string, or repeatedly rescanning the line, will not
pass.

EXAMPLES (every rule above appears at least once)

  Every character is shown as written: a backslash in this file is one backslash character,
  not the start of a Python escape sequence. So "a\\b" is the five characters " a \ b "
  and its token is the three characters a \ b, written ['a\b'] below.

  a b c            -> ['a', 'b', 'c']
  a    b           -> ['a', 'b']
  (empty line)     -> []
  (spaces and tabs)-> []
  --version        -> ['--version']
  'it''s'          -> ['its']
  a''b             -> ['ab']
  '' ''            -> ['', '']
  "" a             -> ['', 'a']
  a"b c"d          -> ['ab cd']
  a"b" "c"d        -> ['ab', 'cd']
  -x"y z"          -> ['-xy z']
  a\ b             -> ['a b']
  \#a              -> ['#a']
  a#b              -> ['a#b']
  a #b             -> ['a']
  #a               -> []
  "a\"b"           -> ['a"b']
  "a\\b"           -> ['a\b']
  "a\qb"           -> ['a\qb']
  'a\b'            -> ['a\b']
  'a#b'            -> ['a#b']
  "a#b"            -> ['a#b']

  a\               -> ValueError
  'abc             -> ValueError
  "abc             -> ValueError
