import unittest

from solution import parse_csv_line


class TestParseCsvLine(unittest.TestCase):
    # Examples from TASK.md
    def test_basic_separators(self):
        self.assertEqual(parse_csv_line('a,b,c'), ['a', 'b', 'c'])

    def test_single_field(self):
        self.assertEqual(parse_csv_line('a'), ['a'])

    def test_empty_field_between_commas(self):
        self.assertEqual(parse_csv_line('a,,b'), ['a', '', 'b'])

    def test_only_commas(self):
        self.assertEqual(parse_csv_line(',,,'), ['', '', '', ''])

    def test_empty_quoted(self):
        self.assertEqual(parse_csv_line('""'), [''])

    def test_unquoted_then_quoted(self):
        self.assertEqual(parse_csv_line('a,"b"'), ['a', 'b'])

    def test_leading_comma(self):
        self.assertEqual(parse_csv_line(',"a"'), ['', 'a'])

    def test_trailing_comma(self):
        self.assertEqual(parse_csv_line('"a",'), ['a', ''])

    def test_comma_inside_quotes(self):
        self.assertEqual(parse_csv_line('"a,b",c'), ['a,b', 'c'])

    def test_space_in_quotes(self):
        self.assertEqual(parse_csv_line('"a b"'), ['a b'])

    def test_comma_only_in_quotes(self):
        self.assertEqual(parse_csv_line('","'), [','])

    def test_escaped_quotes(self):
        self.assertEqual(parse_csv_line('"he said ""hi""",x'), ['he said "hi"', 'x'])

    def test_four_quotes_one_literal(self):
        self.assertEqual(parse_csv_line('""""'), ['"'])

    def test_quote_inside_unquoted_field_is_literal(self):
        self.assertEqual(parse_csv_line('a"b'), ['a"b'])

    def test_quotes_inside_unquoted_field_are_literal(self):
        self.assertEqual(parse_csv_line('a"b"'), ['a"b"'])

    def test_empty_line_is_single_empty_field(self):
        self.assertEqual(parse_csv_line(''), [''])

    # Errors
    def test_unterminated_quoted(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"unterminated')

    def test_character_after_closing_quote(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"x')

    def test_trailing_doubled_quote_is_unterminated(self):
        # "a"" : first closing attempt at idx 2 sees another quote -> literal,
        # field then runs to end of line -> unterminated.
        with self.assertRaises(ValueError):
            parse_csv_line('"a""')

    # Extra edge cases
    def test_quoted_field_with_comma_then_more(self):
        self.assertEqual(parse_csv_line('"a,b",'), ['a,b', ''])

    def test_mixed_quoted_unquoted(self):
        self.assertEqual(parse_csv_line('x,"y,z",w'), ['x', 'y,z', 'w'])

    def test_lone_quote_is_unterminated(self):
        # A line starting with a quote is a quoted field needing a close.
        with self.assertRaises(ValueError):
            parse_csv_line('"')

    def test_quoted_empty_between(self):
        self.assertEqual(parse_csv_line('a,"",b'), ['a', '', 'b'])

    def test_quoted_empty_with_trailing_commas(self):
        self.assertEqual(parse_csv_line('"",,'), ['', '', ''])

    def test_spaces_in_unquoted_preserved(self):
        self.assertEqual(parse_csv_line(' a , b '), [' a ', ' b '])

    def test_only_spaces_between_commas(self):
        self.assertEqual(parse_csv_line(' , '), [' ', ' '])

    def test_quoted_field_followed_by_literal_is_error(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"b"')

    def test_quotes_inside_unquoted_are_literal(self):
        self.assertEqual(parse_csv_line('x"a"b"'), ['x"a"b"'])

    def test_error_unterminated_at_end_after_content(self):
        with self.assertRaises(ValueError):
            parse_csv_line('a,"b')

    def test_error_junk_after_close_before_comma(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"b,c')

    def test_error_junk_after_last_quoted_field(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a" x')

    def test_escaped_quote_at_end_of_field_value(self):
        self.assertEqual(parse_csv_line('""""""'), ['""'])

    def test_many_empty_fields(self):
        self.assertEqual(parse_csv_line('a,,,,b'), ['a', '', '', '', 'b'])

    def test_non_ascii_chars(self):
        self.assertEqual(parse_csv_line('héllo, wörld'), ['héllo', ' wörld'])


if __name__ == '__main__':
    unittest.main()
