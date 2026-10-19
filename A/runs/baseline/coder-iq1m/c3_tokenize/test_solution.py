"""Tests for solution.tokenize(). Backslash counting is written carefully:
in a normal (non-raw) Python string, '\\' is one backslash character.
Run: python3 test_solution.py
"""

import time

from solution import tokenize


def expect(line, wanted):
    got = tokenize(line)
    assert got == wanted, 'input %r -> %r (expected %r)' % (line, got, wanted)


def expect_error(line):
    try:
        got = tokenize(line)
    except ValueError:
        return
    raise AssertionError('input %r unexpectedly gave %r' % (line, got))


def examples():
    # verbatim examples from TASK.md
    expect('a b c', ['a', 'b', 'c'])
    expect('a    b', ['a', 'b'])
    expect('', [])
    expect('   ', [])
    expect('--version', ['--version'])
    expect("'it''s'", ['its'])
    expect("a''b", ['ab'])
    expect("'' ''", ['', ''])
    expect('"" a', ['', 'a'])
    expect('a"b c"d', ['ab cd'])
    expect('a"b" "c"d', ['ab', 'cd'])
    expect('-x"y z"', ['-xy z'])
    expect('a\\ b', ['a b'])            # a backslash space b -> "a b"
    expect('\\#a', ['#a'])
    expect('a#b', ['a#b'])
    expect('a #b', ['a'])
    expect('#a', [])
    expect('"a\\"b"', ['a"b'])
    expect('"a\\\\b"', ['a\\b'])        # " a \ \ b " -> token a \ b
    expect('"a\\qb"', ['a\\qb'])        # " a \ q b " -> 4 chars
    expect("'a\\b'", ['a\\b'])          # ' a \ b ' -> a \ b
    expect("'a#b'", ['a#b'])
    expect('"a#b"', ['a#b'])


def tabs():
    expect('a\tb', ['a', 'b'])
    expect(' \t \t ', [])
    expect('a\tb\tc', ['a', 'b', 'c'])
    expect('a\\\tb', ['a\tb'])          # escaped tab does not separate


def empty_segments():
    expect("''", [''])
    expect('""', [''])
    expect("'' ''\t''", ['', '', ''])
    expect('""""', [''])
    expect("''a''", ['a'])
    expect('""a""b""', ['ab'])
    expect("''''''", [''])              # three adjacent empty segments
    expect("''#a", ['#a'])              # token started by empty segment
    expect("'' #a", [''])               # comment after whitespace


def comments():
    expect('#', [])
    expect('  #whatever', [])
    expect('\t#x', [])
    expect('a # b', ['a'])
    expect('a #b c', ['a'])
    expect('a\t# c', ['a'])
    expect('a#', ['a#'])
    expect('##', [])
    expect("'#'", ['#'])
    expect('"#"', ['#'])
    expect("'a'#b", ['a#b'])
    expect('x-#y', ['x-#y'])
    expect('--#', ['--#'])
    expect('\\#', ['#'])
    expect('a\\#b', ['a#b'])
    expect('\\#\\#', ['##'])


def backslash_escapes():
    expect('\\\\', ['\\'])              # \ \ -> one backslash
    expect('\\ ', [' '])
    expect('\\ b', [' b'])
    expect("a\\'b", ["a'b"])
    expect('a\\"b', ['a"b'])
    expect('\\\\n', ['\\n'])            # \ \ n -> backslash + n
    expect('a\\  b', ['a ', 'b'])       # one escaped space, then a real one
    expect('a\\b', ['ab'])
    expect('\\-\\-x', ['--x'])


def double_quotes():
    expect('"\\\\"', ['\\'])            # " \ \ " -> one backslash
    expect('"\\""', ['"'])
    expect('"a\\"b"', ['a"b'])
    expect('"a\\b"', ['a\\b'])          # unknown escape: \ stays literal
    expect('"\\q"', ['\\q'])
    expect('"a\\$b"', ['a\\$b'])
    expect('"a\\\\b"', ['a\\b'])
    expect('"it\'s"', ["it's"])
    expect('"a b"  c', ['a b', 'c'])
    expect('" "', [' '])
    expect('"" " "', ['', ' '])
    expect('"a""b"', ['ab'])
    expect('""\'\'""', [''])


def single_quotes():
    expect("'\\'", ['\\'])              # backslash is literal inside ' '
    expect("'\\#'", ['\\#'])
    expect("'\"'", ['"'])
    expect("'a b' c", ['a b', 'c'])
    expect("''''", [''])               # two adjacent empty segments
    expect("'a''b'", ['ab'])
    expect("'\"\"'", ['""'])
    expect("'a#' b", ['a#', 'b'])


def adjacency():
    expect("x\"a\"'b'c", ['xabc'])
    expect('"\'"', ["'"])
    expect("'\"'", ['"'])
    expect("a''\"b c\"\\ d", ['ab c d'])
    expect('\\a\\b\\c', ['abc'])


def errors():
    expect_error('a\\')
    expect_error('a \\')
    expect_error(' \\')
    expect_error('\\')
    expect_error("'abc")
    expect_error("'a b")
    expect_error("'a\\")                # \ literal inside single quotes, unclosed
    expect_error("'''")                 # '' closed, then lone ' unclosed
    expect_error('"abc')
    expect_error('"a b')
    expect_error('"a\\"')               # \" escaped, string never closed
    expect_error('"a\\\\')              # \\ escaped, string never closed
    expect_error("'a\"b\\")             # unclosed single quote
    expect_error('"a"b\\')              # trailing backslash at end of line


def perf():
    line = (
        "prog --flag=value 'sq str' \"dq \\\"esc\\\" str\" a\\ b k\\#v a#b"
        "\t\t"
    ) * 4000
    t0 = time.time()
    toks = tokenize(line)
    dt = time.time() - t0
    assert toks and dt < 3.0, 'slow: %.2fs' % dt

    big = 'x' * 200000
    t0 = time.time()
    got = tokenize(big)
    dt = time.time() - t0
    assert got == [big] and dt < 3.0, 'slow: %.2fs' % dt

    seg = "'ab'" * 50000
    t0 = time.time()
    got = tokenize(seg)
    dt = time.time() - t0
    assert got == ['ab' * 50000] and dt < 3.0, 'slow: %.2fs' % dt

    seg = '"a\\"b\\\\c"' * 25000
    t0 = time.time()
    got = tokenize(seg)
    dt = time.time() - t0
    assert got == ['a"b\\c' * 25000] and dt < 3.0, 'slow: %.2fs' % dt

    seg = ('\\ ' * 100000)              # one token of 100000 spaces
    t0 = time.time()
    got = tokenize(seg)
    dt = time.time() - t0
    assert got == [' ' * 100000] and dt < 3.0, 'slow: %.2fs' % dt


if __name__ == '__main__':
    examples()
    tabs()
    empty_segments()
    comments()
    backslash_escapes()
    double_quotes()
    single_quotes()
    adjacency()
    errors()
    perf()
    print('ALL TESTS PASSED')
