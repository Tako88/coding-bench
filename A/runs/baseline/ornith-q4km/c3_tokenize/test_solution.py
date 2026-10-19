from solution import tokenize


def check(line, expected):
    result = tokenize(line)
    assert result == expected, f"line={line!r} got {result!r} expected {expected!r}"


def check_err(line):
    try:
        tokenize(line)
    except ValueError:
        return
    raise AssertionError(f"expected ValueError for {line!r}")


# --- Examples from TASK.md ---
check("a b c", ['a', 'b', 'c'])
check("a    b", ['a', 'b'])
check("", [])
check("      ", [])
check("\t\t", [])
check(" \t a \t ", ['a'])
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

# --- Errors ---
check_err("a\\")
check_err("'abc")
check_err('"abc')

# --- Additional edge cases ---
# comment only with leading whitespace
check("   # comment", [])
# hash inside token not at start
check("foo#bar", ['foo#bar'])
check("  foo #bar baz", ['foo'])
# backslash at end inside double quotes is an escape of the quote -> unterminated
check_err('"a\\"')
# double-quoted with escaped backslash then close
check('"a\\\\"', ['a\\'])
# multiple escapes
check("a\\\\b", ['a\\b'])
# escaped quote in unquoted context
check('a\\"b', ['a"b'])
# empty double quotes only
check('""', [''])
# single then double empty
check("'' \"\"", ['', ''])
# comment after quoted token
check('"x" # comment', ['x'])
# backslash-space keeps following token attached (escaped ws is literal)
check("\\ a", [' a'])
# only spaces/tabs mix
check(" \t \t ", [])
# token with trailing backslash-space-escaped
check("ab\\ cd\\ ef", ['ab cd ef'])
# '#' immediately after a quote char start of token? quote is first char
check('"#"', ['#'])
check("'#'", ['#'])
# double quote with escaped backslash then escaped quote then close
q = chr(34)
d = q + 'a' + chr(92) + chr(92) + chr(34)
check(d, ['a' + chr(92)])
# leading whitespace then comment
check("\t#t", [])

# --- Performance ---
import time
big = ("abc " * 40000)  # 200,000 chars
start = time.time()
res = tokenize(big)
elapsed = time.time() - start
assert elapsed < 3.0, f"too slow: {elapsed}s"
assert len(res) == 40000
assert all(x == 'abc' for x in res)

# performance with quotes and escapes
big2 = ('"a b " "c\\\\d" # comment\n'[:11] + "\0") * 0  # placeholder
big2 = ('"x y " "z\\\\w"\\#') * (200000 // 16 + 1)
big2 = big2[:200000]
start = time.time()
res2 = tokenize(big2)
elapsed2 = time.time() - start
assert elapsed2 < 3.0, f"too slow: {elapsed2}s"

print("ALL TESTS PASSED")
