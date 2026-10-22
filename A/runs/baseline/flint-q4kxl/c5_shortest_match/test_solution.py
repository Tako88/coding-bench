import time
import unittest

from solution import shortest_prefix_match


class TestExamples(unittest.TestCase):
    def test_examples(self):
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
            with self.subTest(pattern=pattern, text=text, expected=expected):
                self.assertEqual(shortest_prefix_match(pattern, text), expected)

    def test_errors(self):
        bad = [
            'a\\',
            '{a,b',
            'a}b',
            '{a,{b}c',
            '{a{b}',
        ]
        for pattern in bad:
            with self.subTest(pattern=pattern):
                with self.assertRaises(ValueError):
                    shortest_prefix_match(pattern, 'ab')


class TestSemantics(unittest.TestCase):
    def test_empty_pattern(self):
        # empty pattern matches the empty prefix
        self.assertEqual(shortest_prefix_match('', ''), 0)
        self.assertEqual(shortest_prefix_match('', 'a'), 0)
        self.assertEqual(shortest_prefix_match('a', ''), -1)

    def test_star_zero_length(self):
        self.assertEqual(shortest_prefix_match('a*', ''), -1)
        self.assertEqual(shortest_prefix_match('a*', 'aa'), 1)
        self.assertEqual(shortest_prefix_match('a*', 'a'), 1)

    def test_star_prefers_smallest_prefix(self):
        self.assertEqual(shortest_prefix_match('*ab', 'abab'), 2)
        self.assertEqual(shortest_prefix_match('ab*', 'abab'), 2)

    def test_group_empty_alternative(self):
        # alternatives: 'a' and empty -> empty alternative allows empty chunk
        self.assertEqual(shortest_prefix_match('{a,}', 'b'), 0)
        self.assertEqual(shortest_prefix_match('{a,}', ''), 0)
        self.assertEqual(shortest_prefix_match('{a,}b', 'ab'), 2)

    def test_group_escaped_comma(self):
        # group alternatives: 'a' or '\,b' (literal comma + b); then literal 'c'
        self.assertEqual(shortest_prefix_match('{a,\\,b}c', 'ac'), 2)
        self.assertEqual(shortest_prefix_match('{a,\\,b}c', 'abc'), 3)

    def test_group_escaped_close_brace(self):
        # group alternatives: 'a' or '\}' (literal brace); then literal 'c'
        self.assertEqual(shortest_prefix_match('{a,\\}}c', '}c'), 2)
        self.assertEqual(shortest_prefix_match('{a,\\}}c', 'ac'), 2)

    def test_group_single_empty_alternative(self):
        self.assertEqual(shortest_prefix_match('{}', 'ab'), 0)
        self.assertEqual(shortest_prefix_match('{,}', 'ab'), 0)

    def test_unescaped_close_brace_error(self):
        with self.assertRaises(ValueError):
            shortest_prefix_match('a}b', 'ab')

    def test_unescaped_open_brace_error(self):
        with self.assertRaises(ValueError):
            shortest_prefix_match('a{b', 'ab')

    def test_dangling_backslash_error(self):
        with self.assertRaises(ValueError):
            shortest_prefix_match('a\\', 'a')

    def test_unterminated_group_error(self):
        with self.assertRaises(ValueError):
            shortest_prefix_match('{a,b', 'ab')

    def test_nested_group_error(self):
        with self.assertRaises(ValueError):
            shortest_prefix_match('{a,{b}c', 'abc')

    def test_performance(self):
        pattern = '*a*b*c*d*e*f*g*h*i*j*k*l*m*n*o*p*'
        text = 'x' * 4000
        start = time.time()
        result = shortest_prefix_match(pattern, text)
        elapsed = time.time() - start
        self.assertLess(elapsed, 10.0)


if __name__ == '__main__':
    unittest.main()
