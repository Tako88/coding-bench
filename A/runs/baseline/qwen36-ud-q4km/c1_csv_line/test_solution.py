import unittest
from solution import parse_csv_line


class TestParseCsvLine(unittest.TestCase):

    def test_single_field(self):
        self.assertEqual(parse_csv_line('a'), ['a'])

    def test_three_fields(self):
        self.assertEqual(parse_csv_line('a,b,c'), ['a', 'b', 'c'])

    def test_empty_fields_between_commas(self):
        self.assertEqual(parse_csv_line('a,,b'), ['a', '', 'b'])

    def test_all_empty_fields(self):
        self.assertEqual(parse_csv_line(',,,'), ['', '', '', ''])

    def test_leading_comma(self):
        self.assertEqual(parse_csv_line(',,'), ['', '', ''])

    def test_trailing_comma(self):
        self.assertEqual(parse_csv_line('a,'), ['a', ''])

    def test_single_comma(self):
        self.assertEqual(parse_csv_line(','), ['', ''])

    def test_empty_line(self):
        self.assertEqual(parse_csv_line(''), [''])

    def test_quoted_single_field(self):
        self.assertEqual(parse_csv_line('"a"'), ['a'])

    def test_quoted_with_spaces(self):
        self.assertEqual(parse_csv_line('"a b"'), ['a b'])

    def test_empty_quoted_field(self):
        self.assertEqual(parse_csv_line('""'), [''])

    def test_quoted_comma(self):
        self.assertEqual(parse_csv_line('","'), [','])

    def test_quoted_field_with_comma_inside(self):
        self.assertEqual(parse_csv_line('"a,b",c'), ['a,b', 'c'])

    def test_mixed_quoted_and_unquoted(self):
        self.assertEqual(parse_csv_line('a,"b"'), ['a', 'b'])

    def test_leading_quoted(self):
        self.assertEqual(parse_csv_line(',"a"'), ['', 'a'])

    def test_trailing_quoted(self):
        self.assertEqual(parse_csv_line('"a",'), ['a', ''])

    def test_escaped_double_quotes(self):
        self.assertEqual(parse_csv_line('"he said ""hi""",x'), ['he said "hi"', 'x'])

    def test_four_double_quotes(self):
        self.assertEqual(parse_csv_line('""""'), ['"'])

    def test_quote_in_unquoted_field(self):
        self.assertEqual(parse_csv_line('a"b'), ['a"b'])

    def test_quote_in_unquoted_field2(self):
        self.assertEqual(parse_csv_line('a"b"'), ['a"b"'])

    def test_unterminated_quoted_field(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"unterminated')

    def test_char_after_closing_quote(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a"x')

    def test_triple_quote_error(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"a""')

    def test_unterminated_at_end_of_line(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"abc')

    def test_error_with_trailing_text(self):
        with self.assertRaises(ValueError):
            parse_csv_line('"hello" world')

    def test_single_quoted_field_with_escaped_quotes_only(self):
        self.assertEqual(parse_csv_line('""""""'), ['""'])

    def test_empty_quoted_then_invalid(self):
        with self.assertRaises(ValueError):
            parse_csv_line('""a')

    def test_multiple_quoted_fields(self):
        self.assertEqual(parse_csv_line('"a","b","c"'), ['a', 'b', 'c'])

    def test_complex_mixed(self):
        self.assertEqual(parse_csv_line('a,"b",c,"d,e",f'), ['a', 'b', 'c', 'd,e', 'f'])

    def test_only_spaces_unquoted(self):
        self.assertEqual(parse_csv_line('   '), ['   '])

    def test_quoted_field_with_spaces(self):
        self.assertEqual(parse_csv_line('"  "'), ['  '])

    def test_escaped_quote_at_end(self):
        self.assertEqual(parse_csv_line('"a""b"'), ['a"b'])

    def test_just_escaped_quotes(self):
        self.assertEqual(parse_csv_line('""""""'), ['""'])



if __name__ == "__main__":
    unittest.main()
