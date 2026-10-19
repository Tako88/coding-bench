"""Tests for solution.tokenize: spec examples, edge cases, errors, perf.

Inputs are written as raw strings (r"...") so every character is exactly as
typed; where a raw string is not possible, characters are concatenated
explicitly (BS = one backslash, TAB = one tab).
"""

import time

import unittest

from solution import tokenize

BS = "\\"   # one backslash character
TAB = "\t"  # one tab character
DQ = '"'
SQ = "'"


SPEC_CASES = [
    # every example from TASK.md (raw string = literal characters)
    ("a b c", ["a", "b", "c"]),
    ("a    b", ["a", "b"]),
    ("", []),
    ("  \t \t\t  ", []),
    ("--version", ["--version"]),
    (r"'it''s'", ["its"]),
    ("a''b", ["ab"]),
    ("'' ''", ["", ""]),
    ('"" a', ["", "a"]),
    (r'a"b c"d', ["ab cd"]),
    (r'a"b" "c"d', ["ab", "cd"]),
    (r'-x"y z"', ["-xy z"]),
    (r"a\ b", ["a b"]),
    (r"\#a", ["#a"]),
    ("a#b", ["a#b"]),
    ("a #b", ["a"]),
    ("#a", []),
    (r'"a\"b"', ['a"b']),
    (r'"a\\b"', [r"a\b"]),
    (r'"a\qb"', [r"a\qb"]),
    (r"'a\b'", [r"a\b"]),
    (r"'a#b'", ["a#b"]),
    (r'"a#b"', ["a#b"]),
]


class SpecExamples(unittest.TestCase):
    def test_examples(self):
        for line, expected in SPEC_CASES:
            with self.subTest(line=line):
                self.assertEqual(tokenize(line), expected)

    def test_error_examples(self):
        for line in ["a" + BS, "'abc", '"abc', BS]:
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    tokenize(line)


class EdgeCases(unittest.TestCase):
    def test_empty_segments(self):
        self.assertEqual(tokenize("''"), [""])
        self.assertEqual(tokenize('""'), [""])
        self.assertEqual(tokenize("'' ''"), ["", ""])
        self.assertEqual(tokenize('"" ""'), ["", ""])
        self.assertEqual(tokenize("''''"), [""])
        self.assertEqual(tokenize('""""'), [""])

    def test_odd_quote_counts_are_errors(self):
        for line in ["'''", '"""', "''x'"]:
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    tokenize(line)

    def test_quote_adjacent_segments(self):
        self.assertEqual(tokenize("a'b'"), ["ab"])
        self.assertEqual(tokenize('a"b"'), ["ab"])
        self.assertEqual(tokenize("a'b'c\"d e\"f"), ["abcd ef"])
        self.assertEqual(tokenize("'a' 'b'"), ["a", "b"])
        self.assertEqual(tokenize("'a b'"), ["a b"])
        self.assertEqual(tokenize("'a''b'"), ["ab"])

    def test_quotes_of_other_kind_inside(self):
        self.assertEqual(tokenize("'a\"b'"), ['a"b'])
        self.assertEqual(tokenize('"a\'b"'), ["a'b"])
        self.assertEqual(tokenize("'a#b'"), ["a#b"])
        self.assertEqual(tokenize('"a#b"'), ["a#b"])
        self.assertEqual(tokenize(r"'a\b'"), [r"a\b"])  # \ is literal in ''
        self.assertEqual(tokenize(r'"a\b"'), [r"a\b"])  # \b: \ and b literal

    def test_unquoted_escaped_chars(self):
        self.assertEqual(tokenize(r"\#a"), ["#a"])
        self.assertEqual(tokenize(r"a\#b"), ["a#b"])
        self.assertEqual(tokenize(r"a\ b"), ["a b"])
        self.assertEqual(tokenize(r"a\ b c"), ["a b", "c"])
        self.assertEqual(tokenize("a" + BS + TAB + "b"), ["a" + TAB + "b"])
        self.assertEqual(tokenize(r"a\'b"), ["a'b"])
        self.assertEqual(tokenize(r'a\"b'), ['a"b'])
        self.assertEqual(tokenize(r"a\\b"), [r"a\b"])   # a,\,\,b -> a\b
        self.assertEqual(tokenize(r"\ "), [" "])
        self.assertEqual(tokenize(r"\\ x"), [BS, "x"])
        self.assertEqual(tokenize(r"\\"), [BS])
        self.assertEqual(tokenize(r"\\\\"), [BS + BS])
        self.assertEqual(tokenize(r"\\  \\"), [BS, BS])
        self.assertEqual(tokenize(r"\\t"), [BS + "t"])
        self.assertEqual(tokenize(BS + TAB), [TAB])
        self.assertEqual(tokenize(BS + " "), [" "])

    def test_comments(self):
        self.assertEqual(tokenize("#a b c"), [])
        self.assertEqual(tokenize("  #a"), [])
        self.assertEqual(tokenize("\t#x"), [])
        self.assertEqual(tokenize("a#b #c"), ["a#b"])
        self.assertEqual(tokenize(r"a\ #b"), ["a #b"])   # escaped ws keeps token open
        self.assertEqual(tokenize(r"\ #"), [" #"])
        self.assertEqual(tokenize("''#a"), ["#a"])        # # is mid-token here
        self.assertEqual(tokenize('""#'), ["#"])
        self.assertEqual(tokenize("'x' #a"), ["x"])
        self.assertEqual(tokenize("#just a comment"), [])

    def test_double_quote_escapes(self):
        # inputs built from explicit characters: DQ + ... + DQ
        self.assertEqual(tokenize('""'), [""])
        self.assertEqual(tokenize(DQ + BS + BS + DQ), [BS])        # \\ -> \
        self.assertEqual(tokenize(DQ + BS + DQ + DQ), [DQ])        # \" -> "
        self.assertEqual(tokenize(DQ + "a" + BS + BS + DQ), ["a" + BS])
        self.assertEqual(tokenize(DQ + BS + DQ + "x" + DQ), [DQ + "x"])
        self.assertEqual(
            tokenize(DQ + "a" + BS + "q" + BS + "r" + DQ),
            ["a" + BS + "q" + BS + "r"])
        self.assertEqual(tokenize(DQ + BS + "a" + DQ), [BS + "a"])
        # \\ followed by a closing quote: the quote closes (not escaped)
        self.assertEqual(tokenize(DQ + "a" + BS + BS + DQ + "x"),
                         ["a" + BS + "x"])
        # \" followed by a closing quote: the quote is escaped -> unclosed
        with self.assertRaises(ValueError):
            tokenize(DQ + "a" + BS + DQ)
        # backslash as last char of a double-quoted string -> error
        with self.assertRaises(ValueError):
            tokenize(DQ + "a" + BS)

    def test_errors_mid_and_end(self):
        for line in ["a'", 'a"', 'a"b', DQ + "a" + BS, SQ + "a" + BS,
                    "a'b", BS, SQ + "a" + SQ + "b" + SQ]:
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    tokenize(line)

    def test_mixed_whitespace(self):
        self.assertEqual(tokenize("a\tb"), ["a", "b"])
        self.assertEqual(tokenize("\ta\t"), ["a"])
        self.assertEqual(tokenize("a \t b"), ["a", "b"])
        # a, \, TAB, b, \, SP, c  ->  single token: a TAB b SP c
        self.assertEqual(
            tokenize("a" + BS + TAB + "b" + BS + " c"),
            ["a" + TAB + "b c"])


class Performance(unittest.TestCase):
    def _timed(self, line):
        t0 = time.perf_counter()
        result = tokenize(line)
        return result, time.perf_counter() - t0

    def test_large_mixed_line(self):
        # unit: a " b \ SP c " d SP -> one token a b \ SP c d, then separator
        unit = "a" + DQ + "b" + BS + " c" + DQ + "d "
        self.assertEqual(len(unit), 9)
        line = unit * 22222 + "  "  # exactly 200000 chars
        result, dt = self._timed(line)
        self.assertEqual(len(line), 200000)
        self.assertEqual(len(result), 22222)
        self.assertTrue(all(t == "ab" + BS + " cd" for t in result))
        self.assertLess(dt, 3.0)

    def test_large_single_quote(self):
        line = SQ + "x" * 199998 + SQ  # 200000 chars
        result, dt = self._timed(line)
        self.assertEqual(result, ["x" * 199998])
        self.assertLess(dt, 3.0)

    def test_large_double_quote_with_escapes(self):
        unit = "q" + BS + "r"  # q \ r : 150000 chars -> every \ is literal
        inner = unit * 50000
        line = DQ + inner + DQ
        result, dt = self._timed(line)
        self.assertEqual(len(line), 150002)
        self.assertEqual(result, [inner])
        self.assertLess(dt, 3.0)

    def test_large_unquoted_run(self):
        line = "abcdefghij" * 20000  # 200000 chars, one token
        result, dt = self._timed(line)
        self.assertEqual(result, ["abcdefghij" * 20000])
        self.assertLess(dt, 3.0)

    def test_many_small_tokens(self):
        line = "a b " * 50000  # 200000 chars
        result, dt = self._timed(line)
        self.assertEqual(result, ["a", "b"] * 50000)
        self.assertLess(dt, 3.0)

    def test_many_escapes_unquoted(self):
        line = ("ab" + BS + " ") * 50000  # 200000 chars; \SP never separates
        result, dt = self._timed(line)
        self.assertEqual(result, ["ab " * 50000])
        self.assertLess(dt, 3.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
