import time
from solution import tokenize


def check(got, expected):
    assert got == expected, f"got {got!r}, expected {expected!r}"


def check_err(line):
    try:
        tokenize(line)
    except ValueError:
        return
    raise AssertionError(f"expected ValueError for {line!r}")


def test_examples():
    check(tokenize("a b c"), ['a', 'b', 'c'])
    check(tokenize("a    b"), ['a', 'b'])
    check(tokenize(""), [])
    check(tokenize("   \t  "), [])
    check(tokenize("--version"), ['--version'])
    check(tokenize("'it''s'"), ['its'])
    check(tokenize("a''b"), ['ab'])
    check(tokenize("'' ''"), ['', ''])
    check(tokenize('"" a'), ['', 'a'])
    check(tokenize('a"b c"d'), ['ab cd'])
    check(tokenize('a"b" "c"d'), ['ab', 'cd'])
    check(tokenize('-x"y z"'), ['-xy z'])
    check(tokenize("a\\ b"), ['a b'])
    check(tokenize("\\#a"), ['#a'])
    check(tokenize("a#b"), ['a#b'])
    check(tokenize("a #b"), ['a'])
    check(tokenize("#a"), [])
    check(tokenize('"a\\"b"'), ['a"b'])
    check(tokenize('"a\\\\b"'), ['a\\b'])
    check(tokenize('"a\\qb"'), ['a\\qb'])
    check(tokenize("'a\\b'"), ['a\\b'])
    check(tokenize("'a#b'"), ['a#b'])
    check(tokenize('"a#b"'), ['a#b'])


def test_errors():
    check_err("a\\")
    check_err("'abc")
    check_err('"abc')


def test_edge():
    # backslash at end inside double quotes
    check_err('"abc\\')
    # escaped quote in double quotes keeps quoting context open
    check_err('"a\\"')
    # backslash escaping a quote in unquoted context
    check(tokenize('a\\"b'), ['a"b'])
    # trailing whitespace
    check(tokenize("a b "), ['a', 'b'])
    check(tokenize("  a  b  "), ['a', 'b'])
    # comment only with leading ws
    check(tokenize("   # comment"), [])
    # multiple comments
    check(tokenize("# a # b"), [])
    # hash inside quotes
    check(tokenize('"#x"'), ['#x'])
    # empty unquoted run between quotes
    check(tokenize("''"), [''])
    check(tokenize('""'), [''])
    # tab separated
    check(tokenize("a\tb"), ['a', 'b'])
    # single quote then unquoted
    check(tokenize("'ab'cd"), ['abcd'])
    # double quote ending then unquoted
    check(tokenize('"ab"cd'), ['abcd'])
    # backslash before hash mid-token (already started) does not comment
    check(tokenize("a\\#b"), ['a#b'])


def test_performance():
    # long unquoted run
    line = "x" * 200000
    t0 = time.time()
    res = tokenize(line)
    dt = time.time() - t0
    assert res == [line], "long unquoted run failed"
    assert dt < 3.0, f"took {dt:.3f}s"

    # long single-quoted content
    line2 = "'" + "y" * 200000 + "'"
    t0 = time.time()
    res2 = tokenize(line2)
    dt = time.time() - t0
    assert res2 == ["y" * 200000]
    assert dt < 3.0, f"took {dt:.3f}s"

    # mix of many tokens
    line3 = " ".join(["tok"] * 50000)
    t0 = time.time()
    res3 = tokenize(line3)
    dt = time.time() - t0
    assert len(res3) == 50000
    assert dt < 3.0, f"took {dt:.3f}s"


if __name__ == "__main__":
    test_examples()
    test_errors()
    test_edge()
    test_performance()
    print("ALL TESTS PASSED")
