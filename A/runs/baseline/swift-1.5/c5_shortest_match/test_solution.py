"""Tests for solution.py (shortest prefix pattern match)."""

import random
import time
import unittest

from solution import shortest_prefix_match, _parse


def _naive_L(atoms, text):
    """Reference implementation: set of L such that the parsed pattern
    matches text[:L].  Simple (potentially exponential) search, only
    used on small inputs."""
    n = len(text)

    def run_alt(alt, j):
        """Positions reachable after consuming atom list `alt` starting
        at position j (alt contains no groups)."""
        pos = {j}
        for a in alt:
            k = a[0]
            nxt = set()
            for p in pos:
                if k == 'lit':
                    if p < n and text[p] == a[1]:
                        nxt.add(p + 1)
                elif k == 'q':
                    if p < n:
                        nxt.add(p + 1)
                else:  # '*'
                    for p2 in range(p, n + 1):
                        nxt.add(p2)
            pos = nxt
            if not pos:
                return frozenset()
        return frozenset(pos)

    steps = []
    for a in atoms:
        if a[0] == 'grp':
            steps.append(('grp', tuple(tuple(x) for x in a[1])))
        else:
            steps.append(('one', (a,)))

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def rec(si, j):
        if si == len(steps):
            return (j,)
        kind, data = steps[si]
        out = set()
        if kind == 'one':
            out.update(run_alt(data, j))
        else:
            for alt in data:
                out.update(run_alt(alt, j))
        res = set()
        for p in out:
            res.update(rec(si + 1, p))
        return tuple(sorted(res))

    return rec(0, 0)


def _random_pattern(rng):
    def gen(in_alt=False):
        r = rng.random()
        if r < 0.40:
            return rng.choice('ab')
        if r < 0.55:
            return '?'
        if r < 0.70:
            return '*'
        if in_alt:
            return '?'  # groups never nest
        alts = []
        for _ in range(rng.randint(1, 3)):
            elems = [gen(True) for _ in range(rng.randint(0, 3))]
            alts.append(''.join(elems))
        return '{' + ','.join(alts) + '}'

    return ''.join(gen() for _ in range(rng.randint(0, 6)))


class ExampleTests(unittest.TestCase):
    def check(self, pattern, text, expected):
        self.assertEqual(shortest_prefix_match(pattern, text), expected,
                         (pattern, text))

    def test_task_examples(self):
        self.check('abc', 'abcdef', 3)
        self.check('a*c', 'abcde', 3)
        self.check('*', 'abc', 0)
        self.check('*', '', 0)
        self.check('a*', 'a', 1)
        self.check('*b', 'aaab', 4)
        self.check('**b', 'ab', 2)
        self.check('{ab,cd}', 'cdx', 2)
        self.check('{a,ab}c', 'abc', 3)
        self.check('{*,a}b', 'ab', 2)
        self.check('{,a}b', 'ab', 2)
        self.check('{}', 'ab', 0)
        self.check('{a,\\{b}c', '{bcd', 3)
        self.check('{\\{a,b}', '{a', 2)
        self.check('a?c', 'abcd', 3)
        self.check('a\\*b', 'a*bc', 3)
        self.check('a', '', -1)
        self.check('abc', 'ab', -1)

    def test_task_value_errors(self):
        for pattern, text in (
            ('a\\', 'a'),
            ('{a,b', 'ab'),
            ('a}b', 'ab'),
            ('{a,{b}c', 'abc'),
            ('{a{b}', 'a{b'),
        ):
            with self.assertRaises(ValueError, msg=pattern):
                shortest_prefix_match(pattern, text)


class EdgeCaseTests(unittest.TestCase):
    def check(self, pattern, text, expected):
        self.assertEqual(shortest_prefix_match(pattern, text), expected,
                         (pattern, text))

    def test_empty_pattern_and_text(self):
        self.check('', '', 0)
        self.check('', 'abc', 0)

    def test_question_mark(self):
        self.check('?', 'a', 1)
        self.check('?', '', -1)
        self.check('?*', 'abc', 1)
        self.check('*?', 'a', 1)

    def test_stars(self):
        self.check('***', 'xyz', 0)
        self.check('*?*', '', -1)
        self.check('a*?', 'a', -1)
        self.check('**b', 'b', 1)

    def test_groups(self):
        self.check('{a*,b*}', 'ab', 1)
        self.check('{a?,b?}', 'b', -1)
        self.check('{a?,b?}', 'ba', 2)
        self.check('{,}', 'x', 0)
        self.check('{a,}', 'a', 0)
        self.check('{a,b}{b,c}', 'ac', 2)
        self.check('{,,}', 'zz', 0)

    def test_escapes(self):
        # pattern 'a\\' is a, backslash  -> literal 'a', literal '\'
        self.check('a\\\\', 'a\\\\', 2)
        self.check('a\\\\', 'a', -1)
        # pattern '\\\\' is two backslashes -> literal '\', literal '\'
        self.check('\\\\\\\\', '\\\\', 2)
        # escaped comma and brace inside a group
        self.check('{\\,\\}}', ',}', 2)
        self.check('{\\,\\}}', ',x', -1)
        # escaped '?', '*'
        self.check('\\?\\*', '?*', 2)
        self.check('\\?\\*', '??', -1)
        self.check('a\\,b', 'a,b', 3)

    def test_more_value_errors(self):
        for pattern in ('\\', '{', '}', '{\\', '{,\\', '{a\\,', '{a,\\}'):
            with self.assertRaises(ValueError, msg=repr(pattern)):
                shortest_prefix_match(pattern, 'x')


class FuzzTests(unittest.TestCase):
    def test_random_against_naive(self):
        rng = random.Random(12345)
        for trial in range(3000):
            pattern = _random_pattern(rng)
            text = ''.join(rng.choice('abc')
                           for _ in range(rng.randint(0, 10)))
            atoms = _parse(pattern)  # generator only makes valid patterns
            Ls = _naive_L(atoms, text)
            expected = min(Ls) if Ls else -1
            got = shortest_prefix_match(pattern, text)
            self.assertEqual(got, expected, (pattern, text))

    def test_random_wider_alphabet(self):
        rng = random.Random(777)
        for trial in range(1000):
            pattern = _random_pattern(rng)
            text = ''.join(rng.choice('ab{}?*\\,')
                           for _ in range(rng.randint(0, 8)))
            atoms = _parse(pattern)
            Ls = _naive_L(atoms, text)
            expected = min(Ls) if Ls else -1
            got = shortest_prefix_match(pattern, text)
            self.assertEqual(got, expected, (pattern, text))


class PerformanceTests(unittest.TestCase):
    def test_large_input(self):
        text = 'a' * 1000 + 'z' * 2000 + 'b' * 1000
        pattern = 'a' * 1000 + '*' * 20 + 'b' * 1000
        start = time.time()
        got = shortest_prefix_match(pattern, text)
        elapsed = time.time() - start
        self.assertEqual(got, 4000)
        self.assertLess(elapsed, 10, "too slow: %.2fs" % elapsed)

    def test_all_stars(self):
        text = 'x' * 4000
        pattern = '*' * 20
        start = time.time()
        got = shortest_prefix_match(pattern, text)
        elapsed = time.time() - start
        self.assertEqual(got, 0)
        self.assertLess(elapsed, 10)

    def test_no_match_large(self):
        text = 'q' * 4000
        pattern = '*' * 20 + 'z'
        got = shortest_prefix_match(pattern, text)
        self.assertEqual(got, -1)

    def test_worst_case_shaped(self):
        # many alternating stars and literals, long text
        text = 'a' * 2000 + 'b' * 2000
        pattern = 'a' * 20 + '*' * 20
        got = shortest_prefix_match(pattern, text)
        self.assertEqual(got, 20)  # 20 literal a's, then stars match zero chars


if __name__ == '__main__':
    unittest.main(verbosity=2)
