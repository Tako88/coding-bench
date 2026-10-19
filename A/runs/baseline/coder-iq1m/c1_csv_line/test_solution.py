"""Tests for solution.parse_csv_line.

Covers every example in TASK.md plus additional edge cases derived from the grammar.
Run with: python3 test_solution.py
"""
import unittest

from solution import parse_csv_line

Q = '"'  # one double quote character


class ParseTests(unittest.TestCase):
    # ---- the examples from TASK.md ----
    def test_examples(self):
        cases = [
            ("a,b,c", ["a", "b", "c"]),
            ("a", ["a"]),
            ("a,,b", ["a", "", "b"]),
            (",,,", ["", "", "", ""]),
            (Q * 2, [""]),
            ("a," + Q + "b" + Q, ["a", "b"]),
            ("," + Q + "a" + Q, ["", "a"]),
            (Q + "a" + Q + ",", ["a", ""]),
            (Q + "a,b" + Q + ",c", ["a,b", "c"]),
            (Q + "a b" + Q, ["a b"]),
            (Q + "," + Q, [","]),
            (Q + 'he said ""hi""' + Q + ",x", ['he said "hi"', "x"]),
            (Q * 4, [Q]),
            ('a"b', ['a"b']),
            ('a"b"', ['a"b"']),
            ("", [""]),
        ]
        for line, expected in cases:
            got = parse_csv_line(line)
            self.assertEqual(got, expected, (line, expected, got))

    # ---- additional valid cases ----
    def test_extra_valid(self):
        cases = [
            ("a,b,", ["a", "b", ""]),
            (",a", ["", "a"]),
            (",,", ["", "", ""]),
            (",", ["", ""]),
            (',"a",,', ["", "a", "", ""]),
            ('a,"",b', ["a", "", "b"]),
            (Q * 2 + "," + Q * 2, ["", ""]),
            ("x," + Q * 2, ["x", ""]),
            (Q * 6, [Q + Q]),  # 6 quotes: two doubled pairs + closing quote
            (Q * 4 + "," + Q * 2, [Q, ""]),  # quoted field, then empty quoted field
            ("x," + Q + 'a""b' + Q + ",y", ["x", 'a"b', "y"]),
            (Q + "a" + Q + ",x", ["a", "x"]),
            (Q + "a" + Q + ',x"', ["a", 'x"']),  # trailing 'x"' is an unquoted field
            (Q + "a" + Q + ', "b"c', ["a", ' "b"c']),  # space-started field is unquoted
            (Q + " " + Q, [" "]),
            ("a," + Q + "b,c" + Q, ["a", "b,c"]),
            ("a," + Q + "b" + Q + ",", ["a", "b", ""]),
            ('a"",b', ['a""', "b"]),  # unquoted field: quotes are literal
            ('a"b"c', ['a"b"c']),  # unquoted: quotes stay literal
            ('a"', ['a"']),  # unquoted: does not start a quoted field
            ('a"b",', ['a"b"', ""]),  # unquoted field then trailing comma
            (Q + 'a""' + Q + ",", ['a"', ""]),  # pair -> literal quote, then closing quote
            (Q + 'a""' + Q + ",x", ['a"', "x"]),
            (Q + "tab\there" + Q + ",z", ["tab\there", "z"]),
        ]
        for line, expected in cases:
            got = parse_csv_line(line)
            self.assertEqual(got, expected, (line, expected, got))

    # ---- error cases ----
    def test_errors(self):
        lines = [
            '"unterminated',  # no closing quote at all
            '"a"x',  # stray character after the closing quote
            Q + "a" + Q * 2,  # doubled pair consumed, nothing closes the field
            Q,  # lone opening quote
            'a,"',  # quoted field with no closing quote
            '"a" ',  # space after the closing quote
            '"a"\t',  # tab after the closing quote
            'a,"b"c',
            Q * 2 + "x",  # empty quoted field, then stray 'x'
            Q + "," + Q + "a",  # quoted field holding a comma, then stray 'a'
            Q * 3,  # opening quote + doubled pair -> unterminated
            Q * 5,  # 5 quotes: two doubled pairs, nothing left to close
            Q + "a" + Q + "*0",  # stray text right after the closing quote
            Q + "a" + Q + "," + Q,  # last field is an unterminated quoted field
            Q + "a" + Q + "," + Q + "b" + Q + "c",  # stray 'c' after second quoted field
            ',"a"b',  # quoted field closes, then 'b' before end of line
        ]
        for line in lines:
            with self.assertRaises(ValueError) as cm:
                parse_csv_line(line)
            self.assertTrue(str(cm.exception), ("message", line))

    def test_empty_line(self):
        self.assertEqual(parse_csv_line(""), [""])

    # ---- encode fields with the quoting rule, then parse them back ----
    def test_roundtrip_simple(self):
        cases = [
            ["a"],
            ["a", "b"],
            ["", ""],
            ['he said "hi"', "x"],
            [","],
            ["a,b", ""],
            [Q, Q + Q],
            ["", ",", "a,b", Q],
            ["x"],
            [Q],
            ["", Q, ""],
            ["sp ace", "tab\there"],
        ]
        for fields in cases:
            parts = []
            for f in fields:
                if f == "" or "," in f or Q in f:
                    parts.append(Q + f.replace(Q, Q + Q) + Q)
                else:
                    parts.append(f)
            line = ",".join(parts)
            self.assertEqual(parse_csv_line(line), fields, (fields, line))

    # ---- field count is (#commas outside quotes) + 1 for quote-free lines ----
    def test_field_count(self):
        for line in ["a", "a,b", "a,,b", ",,,", "x,", ",x,"]:
            self.assertEqual(len(parse_csv_line(line)), line.count(",") + 1, line)


if __name__ == "__main__":
    unittest.main(verbosity=2)
