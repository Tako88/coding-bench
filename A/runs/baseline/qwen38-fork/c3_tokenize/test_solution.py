"""Tests for solution.tokenize: every TASK.md example plus extra edge cases."""
import time

from solution import tokenize


def check(line, expected):
    got = tokenize(line)
    assert got == expected, f"tokenize({line!r}) = {got!r}, expected {expected!r}"


def check_error(line):
    try:
        got = tokenize(line)
    except ValueError:
        return
    raise AssertionError(f"tokenize({line!r}) = {got!r}, expected ValueError")


# ---------------------------------------------------------------- basic runs

def test_basic():
    check("a b c", ['a', 'b', 'c'])
    check("a    b", ['a', 'b'])
    check("", [])
    check("   \t  \t ", [])
    check("\t", [])
    check("--version", ['--version'])
    check("a\tb", ['a', 'b'])
    check("a\t\tb", ['a', 'b'])
    check("-x -y --z", ['-x', '-y', '--z'])


# ------------------------------------------------------------- single quotes

def test_single_quotes():
    check("'it''s'", ['its'])
    check("a''b", ['ab'])
    check("'' ''", ['', ''])
    check("'a\\b'", ['a\\b'])          # backslash inside single quotes is literal
    check("'a#b'", ['a#b'])
    check("'a\\b'", ['a\\b'])          # TASK example: one backslash stays literal
    check("'a\\'", ['a\\'])            # backslash right before closing quote
    check("a'#b'c", ['a#bc'])
    check("'#'", ['#'])
    check("x''y''", ['xy'])
    check("''a''", ['a'])


def test_single_quote_errors():
    check_error("'abc")
    check_error("'")
    check_error("'''")
    check_error("'it's here'")
    check_error(r"\'abc'")             # escaped quote does not open, rest unclosed


# --------------------------------------------------------------- double quotes

def test_double_quotes():
    check('"" a', ['', 'a'])
    check('a"b c"d', ['ab cd'])
    check('a"b" "c"d', ['ab', 'cd'])
    check('-x"y z"', ['-xy z'])
    check('"a\\"b"', ['a"b'])          # \" is one literal "
    check('"a\\\\b"', ['a\\b'])        # \\ is one literal backslash
    check('"a\\qb"', ['a\\qb'])        # any other backslash stays literal
    check('"a#b"', ['a#b'])
    check('"a\\\\"', ['a\\'])         # content is a and one backslash
    check('"a\\\\b"', ['a\\b'])       # TASK example: "a\\b" -> a\b
    check('""""', [''])                # two empty double-quoted segments
    check('""x', ['x'])
    check('x""', ['x'])
    check('"a" b"c"', ['a', 'bc'])
    check('"a\\tb"', ['a\\tb'])        # backslash-t inside double quotes is not an escape
    check('"a\\tb"', ['a\\tb'])        # \\ then t: backslash, t
    check('"#a"', ['#a'])
    check('"a" "b"', ['a', 'b'])


def test_double_quote_errors():
    check_error('"abc')
    check_error('"')
    check_error('"a\\')                # trailing backslash, string never closes
    check_error('"a\\"')               # final " is escaped, so never closed
    check_error('"a \\" b')            # \" inside, then unclosed


# ----------------------------------------------------------------- backslashes

def test_backslashes():
    check('a\\ b', ['a b'])            # escaped space does not separate
    check('\\#a', ['#a'])              # escaped # is literal, token starts at backslash
    check('a\\#b', ['a#b'])
    check('\\ ', [' '])                # escaped space at start of a token
    check('\\\\', ['\\'])              # one literal backslash token
    check('a\\\\ b', ['a\\', 'b'])
    check('\\ta b', ['ta', 'b'])       # backslash-t is a literal t, then a
    check('\\\t a', ['\t', 'a'])       # escaped tab stays inside the token
    check("a\\'b", ['a\'b'])           # escaped quote stays literal in a run
    check('a\\"b', ['a"b'])
    check('\\#a b', ['#a', 'b'])
    check('\\ #a', [' #a'])            # token continues through escaped space


def test_backslash_errors():
    check_error('a\\')
    check_error('\\')
    check_error("x \\")


# ---------------------------------------------------------------------- comments

def test_comments():
    check('a#b', ['a#b'])
    check('a #b', ['a'])
    check('#a', [])
    check('#', [])
    check('#a b c', [])
    check("\t#comment", [])
    check("a\t#b", ['a'])
    check("a'#'", ['a#'])
    check("a'b'#c", ['ab#c'])
    check("'a'# comment", ['a#', 'comment'])  # '#' mid-token is literal, not a comment
    check('a # b', ['a'])
    check('#a b #c', [])


# ------------------------------------------------------------- mixed segments

def test_mixed():
    check("a' ''b'", ['a b'])
    check("a''b''", ['ab'])
    check("'a'\"b\"", ['ab'])
    check("say \"hi\" now", ['say', 'hi', 'now'])
    check("a\"b c\"d", ['ab cd'])
    check("'it''s' \"it's\" fine", ['its', "it's", 'fine'])
    check("x\\'y\\\"", ["x'y\""])    # escaped quote, escaped double quote
    check("'a'\"b\"\"c\"d", ['abcd'])   # empty segment then a quoted one
    check("a'b\"c'd", ['ab"cd'])


# ------------------------------------------------------------------- return type

def test_return_type():
    result = tokenize("a 'b' \"c\"")
    assert isinstance(result, list)
    assert all(isinstance(t, str) for t in result)
    assert result == ['a', 'b', 'c']


# --------------------------------------------------------------------- performance

def test_performance():
    big1 = 'x' * 200000                    # one 200k-char unquoted run
    big2 = ('x ' * 50000)[:-1]             # 50,000 single-char tokens
    big3 = ("'x' " * 50000).strip()        # 50,000 single-quoted tokens
    big4 = ('"x" ' * 50000).strip()        # 50,000 double-quoted tokens
    big7 = ('"x"' * 50000)                 # adjacent quoted segments -> one token
    big5 = ('\\' * 99999) + 'a'            # 100k chars of escapes
    big6 = ('a ' * 40000).strip() + ' # done'  # ends in a comment

    for line in (big1, big2, big3, big4, big5, big6, big7):
        assert len(line) <= 200000, len(line)
        t0 = time.time()
        result = tokenize(line)
        dt = time.time() - t0
        assert dt < 3.0, f'tokenize took {dt:.2f}s for {len(line)} chars'

    assert big1 in ('x' * 200000,) and tokenize(big1) == [big1]
    assert tokenize(big2) == ['x'] * 50000
    assert tokenize(big3) == ['x'] * 50000
    assert tokenize(big4) == ['x'] * 50000
    assert tokenize(big5) == ['\\' * 49999 + 'a']
    assert tokenize(big7) == ['x' * 50000]
    assert tokenize(big6) == ['a'] * 40000


# -------------------------------------------------------------------------- runner

ALL_TESTS = [
    test_basic,
    test_single_quotes,
    test_single_quote_errors,
    test_double_quotes,
    test_double_quote_errors,
    test_backslashes,
    test_backslash_errors,
    test_comments,
    test_mixed,
    test_return_type,
    test_performance,
]


if __name__ == '__main__':
    failed = 0
    for fn in ALL_TESTS:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    if failed:
        raise SystemExit(f"{failed} test function(s) failed")
    print(f"All {len(ALL_TESTS)} test functions passed.")
