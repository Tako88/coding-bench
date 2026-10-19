import unittest

from solution import parse_csv_line


class TestParseCsvLine(unittest.TestCase):
    def check(self, line, expected):
        result = parse_csv_line(line)
        self.assertEqual(result, expected, "parse_csv_line(%r) -> %r, expected %r"
                         % (line, result, expected))
        # Fields must all be strings.
        self.assertTrue(all(isinstance(f, str) for f in result))

    def check_error(self, line):
        with self.assertRaises(ValueError):
            parse_csv_line(line)

    # ---------- examples from TASK.md ----------

    def test_simple_unquoted(self):
        self.check("a,b,c", ['a', 'b', 'c'])
        self.check("a", ['a'])

    def test_empty_fields(self):
        self.check("a,,b", ['a', '', 'b'])
        self.check(",,,", ['', '', '', ''])

    def test_empty_line(self):
        self.check("", [''])

    def test_quoted_fields(self):
        self.check('""', [''])
        self.check('a,"b"', ['a', 'b'])
        self.check(',"a"', ['', 'a'])
        self.check('"a",', ['a', ''])
        self.check('"a,b",c', ['a,b', 'c'])
        self.check('"a b"', ['a b'])
        self.check('","', [','])
        self.check('"he said ""hi""",x', ['he said "hi"', 'x'])
        self.check('""""', ['"'])

    def test_quotes_inside_unquoted_fields(self):
        self.check('a"b', ['a"b'])
        self.check('a"b"', ['a"b"'])

    def test_errors(self):
        self.check_error('"unterminated')
        self.check_error('"a"x')
        self.check_error('"a""')

    # ---------- additional edge cases ----------

    def test_single_quote_is_unterminated(self):
        self.check_error('"')

    def test_runs_of_quotes(self):
        # n quotes: odd n >= 3 -> unterminated; n == 4k -> field of 4k-4
        # ... i.e. opening + (n-2)/2 literal pairs + closing.
        self.check_error('"' * 3)   # opening + pair, no closing
        self.check('"' * 4, ['"'])  # opening + pair + closing
        self.check_error('"' * 5)   # opening + 2 pairs, no closing
        self.check('"' * 6, ['""'])
        self.check_error('"' * 7)
        self.check('"' * 8, ['"""'])
        self.check_error('"' * 9)
        self.check('"' * 10, ['""""'])

    def test_adjacent_quoted_fields(self):
        self.check('"a","b"', ['a', 'b'])
        self.check('""""""', ['""'])

    def test_trailing_commas(self):
        self.check('"a",,b', ['a', '', 'b'])
        self.check('a,,', ['a', '', ''])
        self.check(',', ['', ''])
        self.check(',,', ['', '', ''])

    def test_leading_commas(self):
        self.check(',,a', ['', '', 'a'])
        self.check(',a', ['', 'a'])

    def test_spaces_are_literal(self):
        self.check('a, b', ['a', ' b'])
        self.check(' a ,b ', [' a ', 'b '])

    def test_quote_after_closing_quote_is_error(self):
        self.check_error('""x')
        self.check_error('"""x')

    def test_quote_then_comma_ok(self):
        self.check('"",x', ['', 'x'])
        self.check('"",', ['', ''])

    def test_unquoted_with_embedded_quotes_and_comma(self):
        self.check('a"b,c', ['a"b', 'c'])
        self.check('a"",b', ['a""', 'b'])

    def test_longer_mixed(self):
        self.check('x,"a,b",,"c",d', ['x', 'a,b', '', 'c', 'd'])
        self.check('"","he said ""hi""",a"b"', ['', 'he said "hi"', 'a"b"'])

    def test_lone_quote_is_unterminated(self):
        # A line starting with a quote is a quoted field, so a lone
        # quote has no closing quote.
        self.check_error('"')


if __name__ == "__main__":
    unittest.main(verbosity=2)
