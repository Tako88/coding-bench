import solution
import time


def check(line, expected):
    got = solution.tokenize(line)
    assert got == expected, f"tokenize({line!r}) = {got!r}, expected {expected!r}"


def check_error(line):
    try:
        solution.tokenize(line)
    except ValueError:
        return
    raise AssertionError(f"tokenize({line!r}) should raise ValueError")


def test_examples():
    check("a b c", ['a', 'b', 'c'])
    check("a    b", ['a', 'b'])
    check("", [])
    check("   ", [])
    check("\t\t", [])
    check("--version", ['--version'])
    check("'it''s'", ['its'])
    check("a''b", ['ab'])
    check("'' ''", ['', ''])
    check('"" a', ['', 'a'])
    check('a"b c"d', ['ab cd'])
    check('a"b" "c"d', ['ab', 'cd'])
    check('-x"y z"', ['-xy z'])
    check("a\\ b", ['a b'])
    check("\\#a", ['#a'])
    check("a#b", ['a#b'])
    check("a #b", ['a'])
    check("#a", [])
    check('"a\\"b"', ['a"b'])
    check('"a\\\\b"', ['a\\b'])
    check('"a\\qb"', ['a\\qb'])
    check("'a\\b'", ['a\\b'])
    check("'a#b'", ['a#b'])
    check('"a#b"', ['a#b'])


def test_errors():
    check_error("a\\")
    check_error("'abc")
    check_error('"abc')


def test_empty_tokens_and_quotes():
    check("''", [''])
    check('""', [''])
    check('"a""b"', ['ab'])
    check("a''", ['a'])
    check("''a", ['a'])
    check("a\"\"b", ['ab'])
    check("' '", [' '])
    check('" "', [' '])


def test_comment_rules():
    check("a#b", ['a#b'])
    check("a #b", ['a'])
    check("#a", [])
    check(" #a b", [])
    check("x#y #z", ['x#y'])
    check("a\\#b", ['a#b'])
    check("a \\#b", ['a', '#b'])
    check("'#'x", ['#x'])
    check('"#"x', ['#x'])


def test_escapes():
    check("\\\\", ['\\'])
    check("a\\\\b", ['a\\b'])
    check("\\\\\\a", ['\\a'])
    check('"a\\\\"', ['a\\'])
    check('"a\\"b"', ['a"b'])
    check('"a\\qb"', ['a\\qb'])
    check("'a\\'", ['a\\'])


def test_quoted_hash_not_comment():
    check('"#"', ['#'])
    check("'#'", ['#'])
    check('"a#b"', ['a#b'])


def test_whitespace():
    check("a\tb", ['a', 'b'])
    check("a\\\tb", ['a\tb'])
    check(" \t a \t", ['a'])


def test_unterminated():
    check_error('"abc')
    check_error("'abc")
    check_error('"')
    check_error("'")
    check_error('"a\\')


def test_performance():
    long_line = "a" * 200000
    start = time.time()
    result = solution.tokenize(long_line)
    elapsed = time.time() - start
    assert result == [long_line]
    assert elapsed < 3.0, f"too slow: {elapsed}"


def test_multiple_tokens_performance():
    line = " ".join(["abc"] * 50000)
    start = time.time()
    result = solution.tokenize(line)
    elapsed = time.time() - start
    assert len(result) == 50000
    assert elapsed < 3.0, f"too slow: {elapsed}"


if __name__ == "__main__":
    test_examples()
    test_errors()
    test_empty_tokens_and_quotes()
    test_comment_rules()
    test_escapes()
    test_quoted_hash_not_comment()
    test_whitespace()
    test_unterminated()
    test_performance()
    test_multiple_tokens_performance()
    print("ALL TESTS PASSED")
