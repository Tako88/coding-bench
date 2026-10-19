# shortest prefix pattern match

Implement shortest_prefix_match(pattern, text) in solution.py.

PATTERN LANGUAGE (complete)

  - An ordinary character matches exactly itself.
  - '?' matches exactly one character.
  - '*' matches zero or more characters.
  - '{...}' is a group: it matches exactly one of its comma-separated alternatives. The
    alternatives may each be empty, and may contain ordinary characters, '?' and '*'.
    Braces never nest and an unescaped '{' inside an alternative is an ERROR, not a
    literal and not the start of a nested group: write '\{' to match a brace character.
    The first unescaped '}' closes the group, and ',' separates the alternatives, so a
    literal ',' or '}' inside an alternative must also be escaped ('\,' '\}').
  - '\' makes the character after it an ordinary literal character, so \* \? \{ \} \,
    and \\ match the character itself. A '\' with no character after it is an error.
  - An unescaped '{' with no closing unescaped '}' is an error, and so is an unescaped '{'
    anywhere inside a group alternative. An unescaped '}' with no open group is an error.
    Every malformed pattern raises ValueError.
  - Text and pattern are Python strings: a character is one Python code point, so len()
    counts what you would expect.

SEMANTICS

  The pattern matches text[:L] when the pattern can be read left to right as a sequence of
  pattern elements, each element consuming a contiguous chunk of text[:L], in order, with
  the chunks covering text[:L] exactly and each element matching its own chunk:

    - an ordinary character matches a chunk equal to that one character
    - '?' matches a chunk of exactly one character
    - '*' matches a chunk of any length, including zero
    - a group matches a chunk matched by exactly one of its alternatives, where each
      alternative is itself read as a sequence of elements

  Return the SMALLEST L with 0 <= L <= len(text) for which the pattern matches text[:L], as
  an int. Return -1 when there is no such L.

PERFORMANCE: the pattern may contain up to 20 '*' characters and text may be up to 4000
characters long; the call must finish within 10 seconds. A backtracking matcher that tries
every possible split of every '*' will not finish in time.

EXAMPLES

  Pattern and text are shown as written: a backslash in this file is one backslash
  character, not the start of a Python escape sequence. So '\{' is a backslash followed by
  a brace, and a pattern ending in '\' ends in one backslash character.

  shortest_prefix_match('abc', 'abcdef')   -> 3
  shortest_prefix_match('a*c', 'abcde')    -> 3
  shortest_prefix_match('*', 'abc')        -> 0
  shortest_prefix_match('*', '')           -> 0
  shortest_prefix_match('a*', 'a')         -> 1
  shortest_prefix_match('*b', 'aaab')      -> 4
  shortest_prefix_match('**b', 'ab')       -> 2
  shortest_prefix_match('{ab,cd}', 'cdx')  -> 2
  shortest_prefix_match('{a,ab}c', 'abc')  -> 3
  shortest_prefix_match('{*,a}b', 'ab')    -> 2
  shortest_prefix_match('{,a}b', 'ab')     -> 2
  shortest_prefix_match('{}', 'ab')        -> 0
  shortest_prefix_match('{a,\{b}c', '{bcd') -> 3
  shortest_prefix_match('{\{a,b}', '{a')  -> 2
  shortest_prefix_match('a?c', 'abcd')     -> 3
  shortest_prefix_match('a\*b', 'a*bc')    -> 3
  shortest_prefix_match('a', '')           -> -1
  shortest_prefix_match('abc', 'ab')       -> -1

  shortest_prefix_match('a\', 'a')         -> ValueError
  shortest_prefix_match('{a,b', 'ab')      -> ValueError
  shortest_prefix_match('a}b', 'ab')       -> ValueError
  shortest_prefix_match('{a,{b}c', 'abc')  -> ValueError
  shortest_prefix_match('{a{b}', 'a{b')    -> ValueError
