"""Tests for solution.tokenize covering every TASK.md example and edge cases."""

import time

from solution import tokenize


BS = '\\'  # one backslash


def check(line, expected):
    result = tokenize(line)
    assert result == expected, (
        f"tokenize({line!r}) == {result!r}, expected {expected!r}"
    )


def check_error(line):
    try:
        result = tokenize(line)
    except ValueError:
        return
    raise AssertionError(f"tokenize({line!r}) == {result!r}, expected ValueError")


def test_task_examples():
    # Simple unquoted runs and whitespace.
    check('a b c', ['a', 'b', 'c'])
    check('a    b', ['a', 'b'])
    check('', [])
    check('   \t  ', [])
    check(' \t \t ', [])
    check('--version', ['--version'])

    # Single quotes.
    check("'it''s'", ['its'])
    check("a''b", ['ab'])
    check("'' ''", ['', ''])
    check("''", [''])

    # Double quotes.
    check('"" a', ['', 'a'])
    check('a"b c"d', ['ab cd'])
    check('a"b" "c"d', ['ab', 'cd'])
    check('-x"y z"', ['-xy z'])
    check('""', [''])

    # Backslash escapes in unquoted runs.
    check(r'a\ b', ['a b'])
    check(r'\#a', ['#a'])
    check('a#b', ['a#b'])
    check('a #b', ['a'])

    # Comments.
    check('#a', [])
    check('   # comment', [])
    check('#', [])

    # Backslashes inside double quotes.
    check(r'"a\"b"', ['a"b'])
    check(r'"a\\b"', [r'a\b'])
    check(r'"a\qb"', [r'a\qb'])

    # Backslashes and '#' inside quotes.
    check(r"'a\b'", [r'a\b'])
    check(r"'a#b'", ['a#b'])
    check('"a#b"', ['a#b'])

    # Errors.
    check_error('a\\')
    check_error("'abc")
    check_error('"abc')
    check_error('\\')


def test_edge_cases():
    # Tabs as separators and escapes in unquoted runs.
    check('a\tb', ['a', 'b'])
    check(r'\t', ['t'])
    check(r'a\  b', ['a ', 'b'])
    check(r'\ ', [' '])
    check(r'\  ', [' '])
    check(r'a\tb', ['atb'])

    # Escaped quotes and backslashes in unquoted runs.
    check(r"a\'b", ["a'b"])
    check(r'a\"b', ['a"b'])
    check(r'a\\', ['a\\'])
    check(r'\\', ['\\'])
    check(r'a\\b', [r'a\b'])
    check(r"\'", ["'"])
    check(r'\"', ['"'])
    check(r'\\\\', [r'\\'])
    check('\\\\\\\\', ["\\'"])
    check_error('\\\\\\')
    check(r'a\'', ["a'"])
    check(r'a\"', ['a"'])

    # '#' handling: comment only at first char of a token, literal elsewhere.
    check('#', [])
    check('#abc', [])
    check('a#b', ['a#b'])
    check('a#b#', ['a#b#'])
    check('a #b', ['a'])
    check('a\t#b', ['a'])
    check(r'a\#', ['a#'])
    check(r'a\ #', ['a #'])          # escaped space: token alive, '#' literal
    check(r'a\ #b', ['a #b'])
    check(r'\ #x', [' #x'])          # token started at escaped space
    check(r"\'#", ["'#"])
    check(r"'a'#b", ['a#b'])
    check(r"a'b'#c", ["a'b#c"])
    check(r'"a"#b', ['a#b'])
    check(r'a# #b', ['a#'])
    check("''#x", ['#x'])            # '#' mid-token after empty segment
    check("'' #x", [''])              # '#' after whitespace starts comment
    check('"#"', ['#'])
    check("' # '", [' # '])
    check('" # "', [' # '])
    check('"a#b" #c', ['a#b'])
    check("'a#b' #c", ['a#b'])

    # Empty quoted segments and adjacent segments.
    check("''''", [''])
    check('""""', [''])
    check('"", "b"', ['"', 'b'])
    check("'a'\"b\"", ['ab'])
    check("a'b'c", ['abc'])
    check('"a"b"c"', ['abc'])
    check(r"'\"'", ['"'])
    check('a\'b', ["a'b"])
    check("a'b", ["a'b"])
    check('a"b"', ['ab'])
    check("'a'  ", ['a'])
    check('"a"  ', ['a'])

    # Escapes inside double quotes.
    check(r'"a\ b"', ['a\\ b'])
    check(r'"a\\""', ['a"'])
    check(r'"\\""', ['"'])
    check(r'"a\\b"', [r'a\b'])
    check(r'"a\"b\"c"', ['a"b"c'])
    check(r'"\"a\""', ['"a"'])
    check(r'"a\1b"', ['a\\1b'])
    check(r'"a\#b"', ['a\\#b'])
    check('"\\" #x', ['"'])
    check('"a\\"b"', ['a"b'])

    # Escapes inside single quotes are all literal.
    check(r"'a\\'", [r'a\\'])
    check(r"'a\"'", ['a"'])
    check(r"'a\'", ['a\\'])
    check(r"'\\'", [r'\\'])
    check(r"'a\"b'", ['a"b'])
    check(r"'a\\b'", [r'a\\b'])


def test_errors():
    # Trailing backslash.
    check_error('\\')
    check_error('a\\')
    check_error('a b\\')
    check_error('"a\\')            # trailing backslash inside double quotes
    check_error('a"b\\')
    check_error("'a'\\\"b\\'")

    # Unclosed single quote.
    check_error("'abc")
    check_error("'")
    check_error(r"'abc\"")          # \" literal inside single quotes, unclosed
    check_error(r"'a'b'c")          # last ' opens a new unclosed quote
    check_error(r"'a\"'")           # unclosed single quote
    check_error(r"\"'")             # escaped quote then unclosed single quote

    # Unclosed double quote.
    check_error('"abc')
    check_error('"')
    check_error(r'a"b c')
    check_error(r"'a'b\"")          # ' closes, " opens and never closes
    check_error(r"a'b\"")
    check_error(r'"abc\'')          # ' literal inside double quotes
    check_error(r'"abc\"')          # \" is an escaped quote, still unclosed
    check_error(r'a"b\'c')          # ' literal inside double quotes


def test_performance():
    # 200,000 characters, single token.
    line = 'a' * 200000
    t0 = time.perf_counter()
    result = tokenize(line)
    elapsed = time.perf_counter() - t0
    assert result == [line]
    assert elapsed < 3.0, f"single token took {elapsed:.3f}s"

    # 200,000 characters, 100,000 tokens.
    line = ' '.join(['x'] * 100000)
    t0 = time.perf_counter()
    result = tokenize(line)
    elapsed = time.perf_counter() - t0
    assert len(result) == 100000 and all(t == 'x' for t in result)
    assert elapsed < 3.0, f"many tokens took {elapsed:.3f}s"

    # 200,000 characters of quoted content with escapes.
    line = '"ab\\ \\" "' * 50000
    t0 = time.perf_counter()
    result = tokenize(line)
    elapsed = time.perf_counter() - t0
    assert len(result) == 50000
    assert elapsed < 3.0, f"quoted line took {elapsed:.3f}s"


def main():
    test_task_examples()
    test_edge_cases()
    test_errors()
    test_performance()
    print('All tests passed.')


if __name__ == '__main__':
    main()
