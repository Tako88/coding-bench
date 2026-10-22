import unittest
from solution import parse_csv_line


class TestParseCsvLine(unittest.TestCase):
    def test_examples(self):
        cases = [
            ("a,b,c", ["a", "b", "c"]),
            ("a", ["a"]),
            ("a,,b", ["a", "", "b"]),
            (",,,", ["", "", "", ""]),
            ('""', [""]),
            ('a,"b"', ["a", "b"]),
            (',"a"', ["", "a"]),
            ('"a",', ["a", ""]),
            ('"a,b",c', ["a,b", "c"]),
            ('"a b"', ["a b"]),
            ('"' + ',' + '"', [","]),
            ('"he said ""hi""",x', ['he said "hi"', "x"]),
            ('""""', ['"']),
            ('a"b', ['a"b']),
            ('a"b"', ['a"b"']),
            ("", [""]),
        ]
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertEqual(parse_csv_line(line), expected)

    def test_errors(self):
        bad = [
            '"unterminated',  # missing closing quote
            '"a"x',            # junk after closing quote
            '"a""',            # unterminated via escaped-quote handling
        ]
        for line in bad:
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_csv_line(line)

    def test_empty_fields(self):
        self.assertEqual(parse_csv_line("a,"), ["a", ""])
        self.assertEqual(parse_csv_line(",a"), ["", "a"])
        self.assertEqual(parse_csv_line(",,"), ["", "", ""])
        self.assertEqual(parse_csv_line("a"), ["a"])

    def test_quoted_empty_and_commas(self):
        self.assertEqual(parse_csv_line('"a,b,c"'), ["a,b,c"])
        self.assertEqual(parse_csv_line('""""'), ['"'])
        self.assertEqual(parse_csv_line('"""x"'), ['"x'])

    def test_unquoted_quotes_are_literal(self):
        self.assertEqual(parse_csv_line('ab"cd'), ['ab"cd'])
        self.assertEqual(parse_csv_line('ab"cd"'), ['ab"cd"'])

    def test_quoted_escaped_quotes(self):
        self.assertEqual(parse_csv_line('"a""b""c"'), ['a"b"c'])
        self.assertEqual(parse_csv_line('"say ""hi"" ok"'), ['say "hi" ok'])


if __name__ == "__main__":
    unittest.main()
