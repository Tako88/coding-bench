"""Tests for solution.shortest_prefix_match.

Covers every example from TASK.md, parsing error cases, hand-computed edge
cases, a randomized cross-check against a brute-force backtracking matcher,
and a performance sanity check at the stated limits.
"""

import random
import time
import unittest

from solution import _parse, shortest_prefix_match as m


# ---------------------------------------------------------------- examples


class TestTaskExamples(unittest.TestCase):
    def test_value_examples(self):
        cases = [
            ('abc', 'abcdef', 3),
            ('a*c', 'abcde', 3),
            ('*', 'abc', 0),
            ('*', '', 0),
            ('a*', 'a', 1),
            ('*b', 'aaab', 4),
            ('**b', 'ab', 2),
            ('{ab,cd}', 'cdx', 2),
            ('{a,ab}c', 'abc', 3),
            ('{*,a}b', 'ab', 2),
            ('{,a}b', 'ab', 2),
            ('{}', 'ab', 0),
            ('{a,\\{b}c', '{bcd', 3),
            ('{\\{a,b}', '{a', 2),
            ('a?c', 'abcd', 3),
            ('a\\*b', 'a*bc', 3),
            ('a', '', -1),
            ('abc', 'ab', -1),
        ]
        for pattern, text, expected in cases:
            with self.subTest(pattern=pattern, text=text):
                self.assertEqual(m(pattern, text), expected)

    def test_value_error_examples(self):
        bad = [
            ('a\\', 'a'),
            ('{a,b', 'ab'),
            ('a}b', 'ab'),
            ('{a,{b}c', 'abc'),
            ('{a{b}', 'a{b'),
        ]
        for pattern, text in bad:
            with self.subTest(pattern=pattern, text=text):
                with self.assertRaises(ValueError):
                    m(pattern, text)


# ---------------------------------------------------------------- parsing


class TestParsing(unittest.TestCase):
    def test_more_errors(self):
        bad = [
            ('\\', ''),              # trailing backslash
            ('{', 'x'),              # unterminated group
            ('{a', 'x'),             # unterminated group
            ('{\\', 'x'),            # trailing backslash inside group
            ('{a,\\', 'x'),          # trailing backslash inside group
            ('{a{b', 'x'),           # nested brace, also unterminated
            ('{a,{b}', 'x'),         # brace inside alternative
            ('{a{b}c', 'x'),         # brace inside alternative
            ('{a}}', 'x'),           # extra '}' at top level
            ('{a,}}', 'x'),          # extra '}' at top level
            ('{}}', 'x'),            # extra '}' at top level
            ('}', 'x'),              # lone '}'
            ('a{b', 'x'),            # unterminated group at the end
        ]
        for pattern, text in bad:
            with self.subTest(pattern=pattern):
                with self.assertRaises(ValueError):
                    m(pattern, text)

    def test_escapes_top_level(self):
        cases = [
            ('\\\\', '\\', 1),       # literal backslash
            ('\\\\', 'a', -1),
            ('\\{', '{', 1),          # escaped brace is an ordinary char
            ('\\{', 'a', -1),
            ('\\*', '*', 1),
            ('\\?', '?', 1),
            ('\\,b', ',b', 2),
            ('a\\}b', 'a}b', 3),
            ('\\{a,b', '{a,b', 4),    # top-level , and } are ordinary (no '}')
            ('a\\a', 'aa', 2),        # escaping an ordinary char is allowed
        ]
        for pattern, text, expected in cases:
            with self.subTest(pattern=pattern, text=text):
                self.assertEqual(m(pattern, text), expected)

    def test_escapes_in_groups(self):
        cases = [
            ('{\\,a,b}', ',a', 2),    # one alternative ',a'
            ('{a,\\,b}', ',b', 2),    # alternatives 'a' and ',b'
            ('{a,\\,b}', 'a', 1),
            ('{\\\\,a}', '\\', 1),    # alternatives '\\' and 'a'
            ('{\\\\,a}', 'a', 1),
            ('{a\\},b}', 'a}', 2),    # alternative 'a}'
            ('{a,,b}', 'b', 0),       # empty middle alternative matches ''
            ('{,}a', 'a', 1),         # two empty alternatives
        ]
        for pattern, text, expected in cases:
            with self.subTest(pattern=pattern, text=text):
                self.assertEqual(m(pattern, text), expected)

    def test_groups_adjacent_and_nesting_rules(self):
        cases = [
            ('{a}{b}', 'ab', 2),
            ('{a}{b}', 'a', -1),
            ('{a,ab}{cd}', 'abcd', 4),
            ('{a*b,ab}', 'aab', 3),   # checked by hand
            ('{a*,b}', 'aaab', 1),    # 'a*' already matches 'a'
        ]
        for pattern, text, expected in cases:
            with self.subTest(pattern=pattern, text=text):
                self.assertEqual(m(pattern, text), expected)


# ------------------------------------------------------------ edge values


class TestEdgeValues(unittest.TestCase):
    def test_basics(self):
        cases = [
            ('', '', 0),
            ('', 'abc', 0),
            ('?', 'x', 1),
            ('?', '', -1),
            ('???', 'ab', -1),
            ('***', '', 0),
            ('***', 'zz', 0),
            ('a', 'aa', 1),
            ('*a', 'aaa', 1),
            ('a*a', 'aaa', 2),
            ('*a*', 'ba', 2),
            ('*a*', 'ab', 1),         # L=1: *='', a='a', *=''
            ('a**b', 'ab', 2),
            ('a?*', 'ab', 2),
            ('a?*', 'a', -1),
            ('?*', 'ab', 1),
            ('*?', 'ab', 1),
            ('{a,}b', 'bb', 1),       # empty alternative lets 'b' start at 0
            ('{a,b}*c', 'axc', 3),
            ('*b*b', 'ab', -1),
            ('\uff20?', '\uff20x', 2),
            ('\uff20', '\uff20', 1),
            ('?', '\uff20', 1),
            ('\u00e9b', '\u00e9bc', 2),
            ('a\u00e9b', 'a\u00e9c', -1),
        ]
        for pattern, text, expected in cases:
            with self.subTest(pattern=pattern, text=text):
                self.assertEqual(m(pattern, text), expected)


# ------------------------------------------------- brute force cross-check


def _brute_seq(elements, text, idx, pos, limit):
    """Can elements[idx:] match text[pos:limit] exactly (backtracking)?"""
    if idx == len(elements):
        return pos == limit
    kind = elements[idx][0]
    if kind == 'lit':
        return pos < limit and text[pos] == elements[idx][1] and \
            _brute_seq(elements, text, idx + 1, pos + 1, limit)
    if kind == 'q':
        return pos < limit and _brute_seq(elements, text, idx + 1, pos + 1, limit)
    if kind == 'star':
        return any(_brute_seq(elements, text, idx + 1, j, limit)
                   for j in range(pos, limit + 1))
    # group: some alternative consumes exactly text[pos:j]
    for alt in elements[idx][1]:
        for j in range(pos, limit + 1):
            if _brute_seq(alt, text, 0, pos, j) and \
               _brute_seq(elements, text, idx + 1, j, limit):
                return True
    return False


def brute_shortest(pattern, text):
    elements = _parse(pattern)
    for limit in range(len(text) + 1):
        if _brute_seq(elements, text, 0, 0, limit):
            return limit
    return -1


class TestBruteForceCrossCheck(unittest.TestCase):
    def test_random_agreement(self):
        rng = random.Random(12345)
        for _ in range(400):
            pattern = self.random_pattern(rng)
            text = ''.join(rng.choice('ab*?{,\\')
                           for _ in range(rng.randint(0, 9)))
            expected = brute_shortest(pattern, text)
            with self.subTest(pattern=pattern, text=text):
                self.assertEqual(m(pattern, text), expected)

    @staticmethod
    def random_pattern(rng):
        def alt_body():
            out = []
            for _ in range(rng.randint(0, 3)):
                r = rng.random()
                if r < 0.6:
                    out.append(rng.choice('ab'))
                elif r < 0.8:
                    out.append('?')
                else:
                    out.append('*')
            return ''.join(out)

        parts = []
        for _ in range(rng.randint(0, 6)):
            r = rng.random()
            if r < 0.5:
                c = rng.choice('ab')
                parts.append('\\' + c if rng.random() < 0.15 else c)
            elif r < 0.65:
                parts.append('?')
            elif r < 0.85:
                parts.append('*')
            else:
                alts = [alt_body() for _ in range(rng.randint(1, 3))]
                parts.append('{' + ','.join(alts) + '}')
        return ''.join(parts)


# ------------------------------------------------------------- performance


class TestPerformance(unittest.TestCase):
    def test_stars_dense_text(self):
        # 20 stars; naive backtracking would enumerate ~4000^20 splits.
        text = 'a' * 4000
        pattern = 'a' + '*a' * 20          # 20 stars
        t0 = time.time()
        self.assertEqual(m(pattern, text), 21)
        self.assertLess(time.time() - t0, 10)

    def test_stars_then_rare_char(self):
        text = 'a' * 3999 + 'b'
        pattern = '*' * 20 + 'b'
        t0 = time.time()
        self.assertEqual(m(pattern, text), 4000)
        self.assertLess(time.time() - t0, 10)

    def test_group_alternatives_with_star(self):
        text = 'x' * 4000
        # 20 alternatives of growing length, no stars
        pattern = '{' + ','.join('x' * k for k in range(1, 21)) + '}'
        t0 = time.time()
        self.assertEqual(m(pattern, text), 1)
        self.assertLess(time.time() - t0, 10)


if __name__ == '__main__':
    unittest.main(verbosity=2)
