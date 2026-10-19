import unittest
import time
from solution import tokenize


class TestBasic(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(tokenize("a b c"), ['a', 'b', 'c'])

    def test_multiple_spaces(self):
        self.assertEqual(tokenize("a    b"), ['a', 'b'])

    def test_empty_line(self):
        self.assertEqual(tokenize(""), [])

    def test_spaces_and_tabs(self):
        self.assertEqual(tokenize("   \t  \t  "), [])

    def test_single_token(self):
        self.assertEqual(tokenize("--version"), ['--version'])

    def test_single_token_long(self):
        s = 'a' * 100
        self.assertEqual(tokenize(s), [s])


class TestSingleQuotes(unittest.TestCase):
    def test_concat_single_quotes(self):
        self.assertEqual(tokenize("'it''s'"), ['its'])

    def test_empty_single_quotes(self):
        self.assertEqual(tokenize("'' ''"), ['', ''])

    def test_single_quote_with_backslash(self):
        self.assertEqual(tokenize("'a\\b'"), ['a\\b'])

    def test_single_quote_with_hash(self):
        self.assertEqual(tokenize("'a#b'"), ['a#b'])

    def test_single_quote_no_close(self):
        with self.assertRaises(ValueError):
            tokenize("'abc")

    def test_single_quote_empty(self):
        self.assertEqual(tokenize("''"), [''])

    def test_single_quote_mixed(self):
        self.assertEqual(tokenize("a''b"), ['ab'])


class TestDoubleQuotes(unittest.TestCase):
    def test_escape_double_quote(self):
        self.assertEqual(tokenize('"a\\"b"'), ['a"b'])

    def test_escape_backslash(self):
        self.assertEqual(tokenize('"a\\\\b"'), ['a\\b'])

    def test_other_escape(self):
        self.assertEqual(tokenize('"a\\qb"'), ['a\\qb'])

    def test_hash_in_double_quote(self):
        self.assertEqual(tokenize('"a#b"'), ['a#b'])

    def test_unclosed_double_quote(self):
        with self.assertRaises(ValueError):
            tokenize('"abc')

    def test_empty_double_quote(self):
        self.assertEqual(tokenize('""'), [''])

    def test_double_quote_with_space(self):
        self.assertEqual(tokenize('"" a'), ['', 'a'])

    def test_double_quote_preserves_space(self):
        self.assertEqual(tokenize('-x"y z"'), ['-xy z'])


class TestUnquotedRun(unittest.TestCase):
    def test_backslash_escape_space(self):
        self.assertEqual(tokenize("a\\ b"), ['a b'])

    def test_backslash_escape_hash(self):
        self.assertEqual(tokenize("\\#a"), ['#a'])

    def test_hash_in_middle(self):
        self.assertEqual(tokenize("a#b"), ['a#b'])

    def test_hash_starts_comment(self):
        self.assertEqual(tokenize("a #b"), ['a'])

    def test_hash_alone(self):
        self.assertEqual(tokenize("#a"), [])

    def test_trailing_backslash(self):
        with self.assertRaises(ValueError):
            tokenize("a\\")


class TestAdjacentSegments(unittest.TestCase):
    def test_quoted_then_quoted(self):
        self.assertEqual(tokenize('a"b c"d'), ['ab cd'])

    def test_quoted_then_space_then_quoted(self):
        self.assertEqual(tokenize('a"b" "c"d'), ['ab', 'cd'])

    def test_empty_segments_adjacent(self):
        self.assertEqual(tokenize("a''b"), ['ab'])

    def test_single_then_double(self):
        self.assertEqual(tokenize("'a'\"b\""), ['ab'])

    def test_double_then_single(self):
        self.assertEqual(tokenize('"a"\'b\''), ['ab'])


class TestComments(unittest.TestCase):
    def test_comment_at_start(self):
        self.assertEqual(tokenize("# comment"), [])

    def test_comment_after_space(self):
        self.assertEqual(tokenize("cmd # comment"), ['cmd'])

    def test_comment_after_multi_space(self):
        self.assertEqual(tokenize("cmd   # comment"), ['cmd'])

    def test_hash_not_comment_in_token(self):
        self.assertEqual(tokenize("a#b"), ['a#b'])

    def test_hash_in_single_quote_not_comment(self):
        self.assertEqual(tokenize("'a#b'"), ['a#b'])

    def test_hash_in_double_quote_not_comment(self):
        self.assertEqual(tokenize('"a#b"'), ['a#b'])


class TestEdgeCases(unittest.TestCase):
    def test_only_whitespace(self):
        self.assertEqual(tokenize("   "), [])

    def test_only_tabs(self):
        self.assertEqual(tokenize("\t\t\t"), [])

    def test_mixed_whitespace(self):
        self.assertEqual(tokenize(" \t \t "), [])

    def test_multiple_tokens_whitespace(self):
        self.assertEqual(tokenize("  a  b  "), ['a', 'b'])

    def test_backslash_in_double_quote_non_special(self):
        self.assertEqual(tokenize('"a\\nb"'), ['a\\nb'])

    def test_double_backslash_in_double_quote(self):
        self.assertEqual(tokenize('"a\\\\\\\\b"'), ['a\\\\b'])

    def test_complex_mixed(self):
        self.assertEqual(tokenize('a"b" "c"d'), ['ab', 'cd'])


class TestPerformance(unittest.TestCase):
    def test_long_line(self):
        # Build a 200,000 character line with many simple tokens
        parts = ['hello'] * 40000  # 200,000 chars + spaces
        line = ' '.join(parts)
        start = time.time()
        result = tokenize(line)
        elapsed = time.time() - start
        self.assertLess(elapsed, 3.0, f"Took {elapsed:.3f}s, limit is 3s")
        self.assertEqual(len(result), 40000)

    def test_long_single_token(self):
        line = 'x' * 200000
        start = time.time()
        result = tokenize(line)
        elapsed = time.time() - start
        self.assertLess(elapsed, 3.0, f"Took {elapsed:.3f}s, limit is 3s")
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 200000)

    def test_long_quoted_token(self):
        # A single double-quoted token of 200,000 chars
        line = '"' + 'x' * 199998 + '"'
        start = time.time()
        result = tokenize(line)
        elapsed = time.time() - start
        self.assertLess(elapsed, 3.0, f"Took {elapsed:.3f}s, limit is 3s")
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 199998)


if __name__ == '__main__':
    unittest.main()
