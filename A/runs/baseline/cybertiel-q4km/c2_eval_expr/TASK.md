# arithmetic expression evaluator

Implement evaluate(expr) in solution.py.

Evaluate an arithmetic expression given as a string and return the result as a float.

GRAMMAR (complete; anything not derivable from it is an error)

  expr    := term (('+' | '-') term)*
  term    := unary (('*' | '/') unary)*
  unary   := ('+' | '-')* power
  power   := primary ('^' unary)?          # '^' is right associative
  primary := number | '(' expr ')'
  number  := digit+ ('.' digit+)?          # digits before the dot are required,
                                           # and digits after the dot are required

  - The binary operators + - * / are left associative. '^' is right associative and binds
    tighter than * and /, so 2^3^2 is 512 and 3*(2+1)^2 is 27.
  - Unary minus and unary plus may be repeated and bind looser than '^', so -2^2 is -4 and
    --3 is 3. They may appear wherever an operand is expected, including directly after a
    binary operator (2*-3, 2--3) and as the exponent (2^-3 is 0.125).
  - A decimal literal needs digits on both sides of the dot: 12, 3.5 and 0.25 are valid,
    while 1. and .5 are errors. 0.25 may not be written as .25.
  - The only whitespace character allowed is the space character ' '. Tabs and newlines
    are not allowed anywhere, even between two operators.
  - No two binary operators may be adjacent (1+*2 is an error), no two operands may be
    adjacent (1 2 and 2(3) are errors), and parentheses must be balanced and non-empty.

ERRORS: raise ValueError for every input that is not derivable from the grammar above,
including the empty string, a whitespace-only string, and any character other than digits,
'.', the operators + - * / ^, parentheses and spaces.

  - Division by zero is not a syntax error and must not be turned into a ValueError: the
    exception from the division itself (ZeroDivisionError) propagates out of evaluate.
  - The return value is always a float, so evaluate("3") is 3.0 and evaluate("3").__class__
    is float. A value too large to be represented as a float raises OverflowError: 2^5^5
    is 2^(5^5), which is out of range.
  - A negative base raised to a fractional exponent has no real value and is an error:
    (-8)^0.5 raises ValueError. A negative exponent is fine (-8^-2 is 0.015625) and so is a
    negative base with an integral exponent ((-8)^2 is 64.0).

EXAMPLES

  The input column is the expression as written; the one quoted example is a Python
  literal, so the escape in it is a real tab character.

  1+2*3     -> 7.0
  2^3^2     -> 512.0
  -2^2      -> -4.0
  (-2)^2    -> 4.0
  (1+2)*3   -> 9.0
  10/4      -> 2.5
  1-2-3     -> -4.0
  8/2/2     -> 2.0
  2*-3      -> -6.0
  2--3      -> 5.0
  2^-3      -> 0.125
  --3       -> 3.0
  +3        -> 3.0
  3.5*2     -> 7.0
  2^0.5     -> 2.0**0.5
  3         -> 3.0
  ( 1 + 2 ) -> 3.0

  (empty)   -> ValueError
  "   "     -> ValueError
  1 2       -> ValueError
  1+        -> ValueError
  *2        -> ValueError
  1+*2      -> ValueError
  ()        -> ValueError
  (1+2      -> ValueError
  1)        -> ValueError
  1..2      -> ValueError
  1.        -> ValueError
  .5        -> ValueError
  2(3)      -> ValueError
  abc       -> ValueError
  "1\t+2"   -> ValueError
  1/0       -> ZeroDivisionError
  2^5^5     -> OverflowError
  (-8)^0.5  -> ValueError
