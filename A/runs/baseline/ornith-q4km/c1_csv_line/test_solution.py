import unittest
from solution import parse_csv_line


class TestExamples(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(parse_csv_line("a,b,c"), ['a', 'b', 'c'])
        self.assertEqual(parse_csv_line("a"), ['a'])
        self.assertEqual(parse_csv_line("a,,b"), ['a', '', 'b'])
        self.assertEqual(parse_csv_line(",,,"), ['', '', '', ''])

    def test_quoted(self):
        self.assertEqual(parse_csv_line('""'), [''])
        self.assertEqual(parse_csv_line('a,"b"'), ['a', 'b'])
        self.assertEqual(parse_csv_line(',"a"'), ['', 'a'])
        self.assertEqual(parse_csv_line('"a",'), ['a', ''])
        self.assertEqual(parse_csv_line('"a,b",c'), ['a,b', 'c'])
        self.assertEqual(parse_csv_line('"a b"'), ['a b'])
        self.assertEqual(parse_csv_line('","'), [','])

    def test_escaped_quotes(self):
        self.assertEqual(parse_csv_line('"he said ""hi""",x'), ['he said "hi"', 'x'])
        self.assertEqual(parse_csv_line('""""'), ['"'])

    def test_unquoted_quotes(self):
        self.assertEqual(parse_csv_line('a"b'), ['a"b'])
        self.assertEqual(parse_csv_line('a"b"'), ['a"b"'])

    def test_empty_line(self):
        self.assertEqual(parse_csv_line(''), [''])


class TestErrors(unittest.TestCase):
    def test_unterminated(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"unterminated')

    def test_char_after_close(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"x')

    def test_unterminated_escaped(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a""')


class TestEdge(unittest.TestCase):
    def test_only_empty(self):
        self.assertEqual(parse_csv_line(''), [''])

    def test_trailing_commas(self):
        self.assertEqual(parse_csv_line('a,,'), ['a', '', ''])
        self.assertEqual(parse_csv_line(','), ['', ''])

    def test_leading_and_trailing(self):
        self.assertEqual(parse_csv_line(',a,'), ['', 'a', ''])

    def test_quoted_with_comma_and_quote(self):
        self.assertEqual(parse_csv_line('"a""b"'), ['a"b'])
        self.assertEqual(parse_csv_line('a,"",b'), ['a', '', 'b'])

    def test_empty_quoted_between(self):
        self.assertEqual(parse_csv_line('""""'), ['"'])
        self.assertEqual(parse_csv_line('a,"",b'), ['a', '', 'b'])


if __name__ == '__main__':
    unittest.main()
