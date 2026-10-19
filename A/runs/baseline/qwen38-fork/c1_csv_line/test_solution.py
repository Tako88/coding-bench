"""Tests for solution.parse_csv_line."""

import unittest

from solution import parse_csv_line


class TestExamples(unittest.TestCase):
    """Every example from TASK.md."""

    def test_simple_fields(self):
        self.assertEqual(parse_csv_line('a,b,c'), ['a', 'b', 'c'])

    def test_single_field(self):
        self.assertEqual(parse_csv_line('a'), ['a'])

    def test_empty_field_between(self):
        self.assertEqual(parse_csv_line('a,,b'), ['a', '', 'b'])

    def test_only_separators(self):
        self.assertEqual(parse_csv_line(',,,'), ['', '', '', ''])

    def test_empty_quoted_field(self):
        self.assertEqual(parse_csv_line('""'), [''])

    def test_unquoted_then_quoted(self):
        self.assertEqual(parse_csv_line('a,"b"'), ['a', 'b'])

    def test_leading_empty_then_quoted(self):
        self.assertEqual(parse_csv_line(',"a"'), ['', 'a'])

    def test_quoted_then_trailing_empty(self):
        self.assertEqual(parse_csv_line('"a",'), ['a', ''])

    def test_comma_inside_quotes(self):
        self.assertEqual(parse_csv_line('"a,b",c'), ['a,b', 'c'])

    def test_space_inside_quotes(self):
        self.assertEqual(parse_csv_line('"a b"'), ['a b'])

    def test_comma_alone_quoted(self):
        self.assertEqual(parse_csv_line('","'), [','])

    def test_escaped_quotes(self):
        self.assertEqual(parse_csv_line('"he said ""hi""",x'), ['he said "hi"', 'x'])

    def test_four_quotes_one_field(self):
        self.assertEqual(parse_csv_line('""""'), ['"'])

    def test_quote_inside_unquoted_is_literal(self):
        self.assertEqual(parse_csv_line('a"b'), ['a"b'])

    def test_quote_inside_unquoted_with_trailing_quote(self):
        self.assertEqual(parse_csv_line('a"b"'), ['a"b"'])

    def test_empty_line_is_single_empty_field(self):
        self.assertEqual(parse_csv_line(''), [''])


class TestErrorCases(unittest.TestCase):
    """Every error example from TASK.md, plus close variants."""

    def test_unterminated(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"unterminated')

    def test_char_after_closing_quote(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"x')

    def test_escaped_quote_left_unterminated(self):
        # "a"" : a, then "" is a literal quote, then end of line: unterminated.
        with self.assertRaises(ValueError):
            parse_csv_line('"a""')

    def test_three_quotes_unterminated(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"""')

    def test_junk_after_empty_quoted_field(self):
        with self.assertRaises(ValueError):
            parse_csv_line('""a')

    def test_junk_after_quoted_field_before_comma(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"b,c')

    def test_unterminated_after_comma(self):
        with self.assertRaises(ValueError):
            parse_csv_line('a,"b')

    def test_char_after_closing_quote_at_end(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"b')


class TestExtraEdgeCases(unittest.TestCase):
    """Additional edge cases derived from the grammar."""

    def test_six_quotes_two_literal_quotes(self):
        self.assertEqual(parse_csv_line('""""""'), ['""'])

    def test_eight_quotes_three_literal_quotes(self):
        self.assertEqual(parse_csv_line('""""""""'), ['"""'])

    def test_quote_pair_then_close(self):
        self.assertEqual(parse_csv_line('""""',), ['"'])

    def test_quoted_comma_only(self):
        self.assertEqual(parse_csv_line('","'), [','])

    def test_quoted_only_commas(self):
        self.assertEqual(parse_csv_line('"a,,b"'), ['a,,b'])

    def test_mixed_multi_field(self):
        self.assertEqual(
            parse_csv_line('x,"a,b",,"c ""d""",'),
            ['x', 'a,b', '', 'c "d"', ''],
        )

    def test_trailing_unquoted_single_quote_char(self):
        self.assertEqual(parse_csv_line('a"'), ['a"'])

    def test_leading_quote_opens_quoted_field(self):
        # A quote as the very first character of the line opens a quoted
        # field, so a quote then end-of-line with no closer is unterminated.
        with self.assertRaises(ValueError):
            parse_csv_line('"a')

    def test_unquoted_field_with_quote_in_middle(self):
        self.assertEqual(parse_csv_line('a"b,c'), ['a"b', 'c'])

    def test_comma_only_line(self):
        self.assertEqual(parse_csv_line(','), ['', ''])

    def test_spaces_are_literal(self):
        self.assertEqual(parse_csv_line('  a , b  '), ['  a ', ' b  '])

    def test_quoted_space_only(self):
        self.assertEqual(parse_csv_line('" "'), [' '])

    def test_quote_pair_only_inside_quoted(self):
        self.assertEqual(parse_csv_line('""""'), ['"'])

    def test_no_newline_assumed(self):
        # Grammar says input never contains a newline; a stray one is just
        # an ordinary character.
        self.assertEqual(parse_csv_line('a\nb'), ['a\nb'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
