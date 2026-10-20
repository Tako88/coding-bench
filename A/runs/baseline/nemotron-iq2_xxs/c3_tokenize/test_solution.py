import unittest
from solution import tokenize


class TestTokenize(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(tokenize('a b c'), ['a', 'b', 'c'])
        self.assertEqual(tokenize('a    b'), ['a', 'b'])
        self.assertEqual(tokenize(''), [])
        self.assertEqual(tokenize('   \t  '), [])
        self.assertEqual(tokenize('--version'), ['--version'])

    def test_tabs(self):
        self.assertEqual(tokenize('a\tb'), ['a', 'b'])
        self.assertEqual(tokenize('a \t b'), ['a', 'b'])

    def test_quotes(self):
        self.assertEqual(tokenize("'it''s'"), ['its'])
        self.assertEqual(tokenize("a''b"), ['ab'])
        self.assertEqual(tokenize("'' ''"), ['', ''])
        self.assertEqual(tokenize('"" a'), ['', 'a'])
        self.assertEqual(tokenize(r'a"b c"d'), ['ab cd'])
        self.assertEqual(tokenize(r'a"b" "c"d'), ['ab', 'cd'])
        self.assertEqual(tokenize(r'-x"y z"'), ['-xy z'])

    def test_backslash(self):
        self.assertEqual(tokenize(r'a\ b'), ['a b'])
        self.assertEqual(tokenize(r'\#a'), ['#a'])
        # backslash drops itself and keeps the next char literally
        self.assertEqual(tokenize(r'a\qb'), ['aqb'])
        self.assertEqual(tokenize(r'a\\\b'), [r'a\b'])
        # escaped tab does not separate tokens
        self.assertEqual(tokenize('a\\\tb'), ['a\tb'])
        # backslash escaping a quote in an unquoted run
        self.assertEqual(tokenize(r'a\"b'), ['a"b'])

    def test_comments(self):
        self.assertEqual(tokenize('a#b'), ['a#b'])
        self.assertEqual(tokenize('a #b'), ['a'])
        self.assertEqual(tokenize('#a'), [])
        self.assertEqual(tokenize('   #a'), [])
        self.assertEqual(tokenize('#'), [])
        # '#' first char of a token starts a comment to end of line
        self.assertEqual(tokenize('a # b c'), ['a'])

    def test_quotes_escapes(self):
        self.assertEqual(tokenize(r'"a\"b"'), ['a"b'])
        self.assertEqual(tokenize(r'"a\\b"'), ['a\\b'])
        self.assertEqual(tokenize(r'"a\qb"'), [r'a\qb'])
        self.assertEqual(tokenize("'a\\b'"), ['a\\b'])
        self.assertEqual(tokenize("'a#b'"), ['a#b'])
        self.assertEqual(tokenize(r'"a#b"'), ['a#b'])

    def test_adjacent_segments(self):
        self.assertEqual(tokenize(r'a"b"c'), ['abc'])
        self.assertEqual(tokenize("'a'b"), ['ab'])
        self.assertEqual(tokenize('""""'), [''])  # two adjacent empty segments

    def test_errors(self):
        with self.assertRaises(ValueError):
            tokenize('a\\')  # backslash at end of line
        with self.assertRaises(ValueError):
            tokenize("'abc")  # single quote never closed
        with self.assertRaises(ValueError):
            tokenize('"abc')  # double quote never closed
        with self.assertRaises(ValueError):
            tokenize('"a\\')  # backslash at end inside double quotes
        with self.assertRaises(ValueError):
            tokenize('"a\\\\')  # double quote never closed

    def test_empty_tokens(self):
        self.assertEqual(tokenize("''"), [''])
        self.assertEqual(tokenize('""'), [''])
        self.assertEqual(tokenize('"" ""'), ['', ''])

    def test_performance(self):
        import time
        line = 'a ' * 100000  # 200,000 characters
        start = time.time()
        result = tokenize(line)
        elapsed = time.time() - start
        self.assertEqual(result, ['a'] * 100000)
        self.assertLess(elapsed, 3.0)


if __name__ == '__main__':
    unittest.main()
