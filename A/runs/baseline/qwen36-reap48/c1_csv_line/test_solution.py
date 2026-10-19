"""Tests for parse_csv_line."""
import unittest
from solution import parse_csv_line


class TestBasicFields(unittest.TestCase):
    def test_simple_fields(self):
        self.assertEqual(parse_csv_line("a,b,c"), ['a', 'b', 'c'])

    def test_single_field(self):
        self.assertEqual(parse_csv_line("a"), ['a'])

    def test_empty_field_between_commas(self):
        self.assertEqual(parse_csv_line("a,,b"), ['a', '', 'b'])

    def test_all_empty_fields(self):
        self.assertEqual(parse_csv_line(",,,") , ['', '', '', ''])

    def test_empty_line(self):
        self.assertEqual(parse_csv_line(""), [''])


class TestQuotedFields(unittest.TestCase):
    def test_quoted_field(self):
        self.assertEqual(parse_csv_line('a,"b"'), ['a', 'b'])

    def test_empty_quoted_field(self):
        self.assertEqual(parse_csv_line('""'), [''])

    def test_comma_in_quoted_field(self):
        self.assertEqual(parse_csv_line('"a,b",c'), ['a,b', 'c'])

    def test_space_in_quoted_field(self):
        self.assertEqual(parse_csv_line('"a b"'), ['a b'])

    def test_quoted_comma_only(self):
        self.assertEqual(parse_csv_line('","'), [','])

    def test_escaped_quotes(self):
        self.assertEqual(parse_csv_line('"he said ""hi""",x'), ['he said "hi"', 'x'])

    def test_four_double_quotes(self):
        self.assertEqual(parse_csv_line('""""'), ['"'])

    def test_quoted_field_then_comma(self):
        self.assertEqual(parse_csv_line('"a",'), ['a', ''])

    def test_field_starting_with_quote(self):
        # After comma, field starts with space (not quote), so it's unquoted
        self.assertEqual(parse_csv_line(', "a"'), ['', ' "a"'])


class TestUnquotedQuotes(unittest.TestCase):
    def test_double_quote_in_unquoted(self):
        self.assertEqual(parse_csv_line('a"b'), ['a"b'])

    def test_double_quote_in_unquoted_end(self):
        self.assertEqual(parse_csv_line('a"b"'), ['a"b"'])


class TestEdgeCases(unittest.TestCase):
    def test_single_quoted_field(self):
        self.assertEqual(parse_csv_line('"hello"'), ['hello'])

    def test_trailing_comma(self):
        self.assertEqual(parse_csv_line("a,"), ['a', ''])

    def test_leading_comma(self):
        self.assertEqual(parse_csv_line(",a"), ['', 'a'])

    def test_only_commas(self):
        self.assertEqual(parse_csv_line(","), ['', ''])

    def test_multiple_quoted(self):
        self.assertEqual(parse_csv_line('"a","b","c"'), ['a', 'b', 'c'])

    def test_empty_quoted_between_commas(self):
        self.assertEqual(parse_csv_line(',"",c'), ['', '', 'c'])

    def test_quoted_with_escaped_quote_at_end(self):
        self.assertEqual(parse_csv_line('"a""b"'), ['a"b'])

    def test_single_double_quote_in_unquoted_field(self):
        self.assertEqual(parse_csv_line('a"'), ['a"'])

    def test_single_double_quote_is_unterminated_quoted(self):
        # A single " starts a quoted field which is never closed
        with self.assertRaises(ValueError):
            parse_csv_line('"')


class TestErrors(unittest.TestCase):
    def test_unterminated_quoted_field(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"unterminated')

    def test_char_after_closing_quote(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"x')

    def test_escaped_quote_then_unterminated(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a""')

    def test_char_after_closing_quote_space(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"x')

    def test_char_after_closing_quote_number(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"1')


if __name__ == '__main__':
    unittest.main()
