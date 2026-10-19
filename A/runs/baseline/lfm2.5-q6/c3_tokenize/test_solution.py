import pytest
from solution import tokenize


def test_basic_split():
    assert tokenize("a b c") == ['a', 'b', 'c']
    assert tokenize("a    b") == ['a', 'b']


def test_empty_and_whitespace():
    assert tokenize("") == []
    assert tokenize("   ") == []
    assert tokenize("\t") == []
    assert tokenize("  \t  ") == []


def test_special_tokens():
    assert tokenize("--version") == ['--version']
    assert tokenize("a#b") == ['a#b']
    assert tokenize("a #b") == ['a']
    assert tokenize("#a") == []


def test_single_quotes():
    assert tokenize("'it''s'") == ['its']
    assert tokenize("a''b") == ['ab']
    assert tokenize("'a\\'b'") == ['a\'b']


def test_double_quotes():
    assert tokenize('"" a') == ['', 'a']
    assert tokenize('"a\\"b"') == ['a"b']
    assert tokenize('"a\\b"') == ['a\b']
    assert tokenize('"a\\qb"') == ['a\\qb']
    assert tokenize("'a\\'b'") == ['a#b']


def test_escaped_whitespace():
    assert tokenize("a\\ b") == ['a b']
    with pytest.raises(ValueError):
        tokenize("a\\")


def test_backslash_at_end():
    with pytest.raises(ValueError):
        tokenize("a\\")


def test_unclosed_quotes():
    with pytest.raises(ValueError):
        tokenize("'abc")
    with pytest.raises(ValueError):
        tokenize('"abc')


def test_comment_in_middle():
    assert tokenize("a#b") == ['a#b']
    assert tokenize("a #b") == ['a']


def test_all_examples():
    # Every example from the specification
    assert tokenize("a b c") == ['a', 'b', 'c']
    assert tokenize("a    b") == ['a', 'b']
    assert tokenize("") == []
    assert tokenize("   ") == []
    assert tokenize("--version") == ['--version']
    assert tokenize("'it''s'") == ['its']
    assert tokenize("a''b") == ['ab']
    assert tokenize("'' ''") == ['', '']
    assert tokenize('"" a') == ['', 'a']
    assert tokenize("a\"b c\"d") == ['ab cd']
    assert tokenize("a\"b\" \"c\"d") == ['ab', 'cd']
    assert tokenize("-x\"y z\"") == ['-xy z']
    assert tokenize("a\\ b") == ['a b']
    assert tokenize("\\#a") == ['#a']
    assert tokenize("a#b") == ['a#b']
    assert tokenize("a #b") == ['a']
    assert tokenize("#a") == []
    assert tokenize('"a\\"b"') == ['a"b']
    assert tokenize('"a\\b"') == ['a\b']
    assert tokenize('"a\qb"') == ['a\qb']
    assert tokenize("'a\\b'") == ['a\b']
    assert tokenize("'a#b'") == ['a#b']
    assert tokenize('"a#b"') == ['a#b']


def test_escaped_backslash_in_double():
    # "a\\b" (4 chars: a, \, b) -> token is 'a\b' (3 chars)
    result = tokenize('"a\\b"')
    assert result == ['a\\b']


def test_empty_segments():
    assert tokenize("'' ''") == ['', '']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
