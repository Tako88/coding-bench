import unittest
from solution import parse_csv_line


class TestExamples(unittest.TestCase):
    def test_examples(self):
        cases = [
            ("a,b,c", ['a', 'b', 'c']),
            ("a", ['a']),
            ("a,,b", ['a', '', 'b']),
            (",,,", ['', '', '', '']),
            ('""', ['']),
            ('a,"b"', ['a', 'b']),
            (',"a"', ['', 'a']),
            ('"a",', ['a', '']),
            ('"a,b",c', ['a,b', 'c']),
            ('"a b"', ['a b']),
            ('","', [',']),
            ('"he said ""hi""",x', ['he said "hi"', 'x']),
            ('""""', ['"']),
            ('a"b', ['a"b']),
            ('a"b"', ['a"b"']),
            ("", ['']),
        ]
        for line, expected in cases:
            with self.subTest(line=repr(line)):
                self.assertEqual(parse_csv_line(line), expected)

    def test_errors(self):
        for line in ['"unterminated', '"a"x', '"a""']:
            with self.subTest(line=repr(line)):
                with self.assertRaises(ValueError):
                    parse_csv_line(line)


class TestEdgeCases(unittest.TestCase):
    def test_many_quoted_escaped(self):
        self.assertEqual(parse_csv_line('""""""'), ['""'])

    def test_only_commas(self):
        self.assertEqual(parse_csv_line(','), ['', ''])

    def test_trailing_commas(self):
        self.assertEqual(parse_csv_line('a,,,'), ['a', '', '', ''])

    def test_leading_commas(self):
        self.assertEqual(parse_csv_line(',,,a'), ['', '', '', 'a'])

    def test_double_quote_in_unquoted(self):
        self.assertEqual(parse_csv_line('x"y"z'), ['x"y"z'])

    def test_empty_quoted_between_commas(self):
        self.assertEqual(parse_csv_line(',"",,'), ['', '', '', ''])

    def test_char_after_closing_quote(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"b')
        with self.assertRaises(ValueError):
            parse_csv_line('"a" ')


if __name__ == '__main__':
    unittest.main()
