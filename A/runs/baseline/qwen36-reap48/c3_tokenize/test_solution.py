"""Tests for solution.py tokenize function."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from solution import tokenize

def test_basic():
    assert tokenize("a b c") == ['a', 'b', 'c']
    assert tokenize("a    b") == ['a', 'b']
    assert tokenize("") == []
    assert tokenize("   ") == []
    assert tokenize("\t\t") == []
    assert tokenize("  \t  ") == []
    assert tokenize("--version") == ['--version']

def test_single_quotes():
    # 'it''s' -> its
    assert tokenize("'it''s'") == ['its']
    # 'a\b' -> a\b  (backslash is literal in single quotes)
    assert tokenize("'a\\b'") == ['a\\b']
    # 'a#b' -> a#b
    assert tokenize("'a#b'") == ['a#b']

def test_double_quotes():
    # "" a -> ['', 'a']
    assert tokenize('"" a') == ['', 'a']
    # "a\"b" -> a"b  (escaped quote)
    assert tokenize('"a\\"b"') == ['a"b']
    # "a\\b" -> a\b  (escaped backslash)
    assert tokenize('"a\\\\b"') == ['a\\b']
    # "a\qb" -> a\qb  (other escape keeps both chars)
    assert tokenize('"a\\qb"') == ['a\\qb']
    # "a#b" -> a#b
    assert tokenize('"a#b"') == ['a#b']

def test_empty_segments():
    assert tokenize("a''b") == ['ab']
    assert tokenize("'' ''") == ['', '']

def test_double_quoted_unquoted_mixed():
    assert tokenize('a"b c"d') == ['ab cd']
    assert tokenize('a"b" "c"d') == ['ab', 'cd']
    assert tokenize('-x"y z"') == ['-xy z']

def test_backslash_escapes():
    assert tokenize('a\\ b') == ['a b']

def test_comments():
    assert tokenize("\\#a") == ['#a']
    assert tokenize("a#b") == ['a#b']
    assert tokenize("a #b") == ['a']
    assert tokenize("#a") == []

def test_error_cases():
    # a\
    try:
        tokenize("a\\")
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    # 'abc
    try:
        tokenize("'abc")
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    # "abc
    try:
        tokenize('"abc')
        assert False, "Should raise ValueError"
    except ValueError:
        pass

def test_edge_cases():
    # Single quoted empty
    assert tokenize("''") == ['']
    # Double quoted empty
    assert tokenize('""') == ['']
    # Escaped quote in double quotes
    assert tokenize('"a\\"b"') == ['a"b']
    # Escaped backslash in double quotes
    assert tokenize('"a\\\\b"') == ['a\\b']
    # Backslash at end of single quoted (just literal backslash, quote closes)
    assert tokenize("'a\\'") == ['a\\']
    # Multiple backslashes
    assert tokenize('"a\\\\\\\\b"') == ['a\\\\b']
    # Escaped backslash followed by quote
    assert tokenize('"a\\\\\\"b"') == ['a\\"b']
    # Tab as separator
    assert tokenize("a\tb") == ['a', 'b']
    # Mixed whitespace
    assert tokenize("a \t b") == ['a', 'b']

def test_complex():
    # Unquoted run with escaped quote
    assert tokenize('a\\"b') == ['a"b']
    # Comment after token
    assert tokenize("foo # comment") == ['foo']
    # Multiple tokens with quotes
    assert tokenize("'hello world' foo") == ['hello world', 'foo']
    # Double quotes with escaped backslash and quote
    assert tokenize('"a\\"b\\\\c"') == ['a"b\\c']

def test_all_task_examples():
    """Every example from TASK.md."""
    # a b c
    assert tokenize("a b c") == ['a', 'b', 'c']
    # a    b
    assert tokenize("a    b") == ['a', 'b']
    # (empty line)
    assert tokenize("") == []
    # (spaces and tabs)
    assert tokenize("   \t  ") == []
    # --version
    assert tokenize("--version") == ['--version']
    # 'it''s'
    assert tokenize("'it''s'") == ['its']
    # a''b
    assert tokenize("a''b") == ['ab']
    # '' ''
    assert tokenize("'' ''") == ['', '']
    # "" a
    assert tokenize('"" a') == ['', 'a']
    # a"b c"d
    assert tokenize('a"b c"d') == ['ab cd']
    # a"b" "c"d
    assert tokenize('a"b" "c"d') == ['ab', 'cd']
    # -x"y z"
    assert tokenize('-x"y z"') == ['-xy z']
    # a\ b
    assert tokenize('a\\ b') == ['a b']
    # \#a
    assert tokenize('\\#a') == ['#a']
    # a#b
    assert tokenize('a#b') == ['a#b']
    # a #b
    assert tokenize('a #b') == ['a']
    # #a
    assert tokenize('#a') == []
    # "a\"b"
    assert tokenize('"a\\"b"') == ['a"b']
    # "a\\b"
    assert tokenize('"a\\\\b"') == ['a\\b']
    # "a\qb"
    assert tokenize('"a\\qb"') == ['a\\qb']
    # 'a\b'
    assert tokenize("'a\\b'") == ['a\\b']
    # 'a#b'
    assert tokenize("'a#b'") == ['a#b']
    # "a#b"
    assert tokenize('"a#b"') == ['a#b']

def test_error_examples():
    """Error examples from TASK.md."""
    # a\
    try:
        tokenize("a\\")
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    # 'abc
    try:
        tokenize("'abc")
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    # "abc
    try:
        tokenize('"abc')
        assert False, "Should raise ValueError"
    except ValueError:
        pass

def test_unclosed_quote_at_end():
    """Unclosed quotes at end of string."""
    try:
        tokenize("'")
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    try:
        tokenize('"')
        assert False, "Should raise ValueError"
    except ValueError:
        pass

def test_backslash_at_end_in_double_quotes():
    """Backslash at end inside double quotes is an error."""
    try:
        tokenize('"a\\')
        assert False, "Should raise ValueError"
    except ValueError:
        pass

def run_all():
    passed = 0
    failed = 0
    for name, func in list(globals().items()):
        if name.startswith('test_') and callable(func):
            try:
                func()
                print(f"  PASS: {name}")
                passed += 1
            except Exception as e:
                print(f"  FAIL: {name}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    run_all()
