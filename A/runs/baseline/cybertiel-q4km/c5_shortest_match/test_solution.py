import unittest

from solution import shortest_prefix_match


class TestExamples(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(shortest_prefix_match('abc', 'abcdef'), 3)
        self.assertEqual(shortest_prefix_match('a*c', 'abcde'), 3)
        self.assertEqual(shortest_prefix_match('*', 'abc'), 0)
        self.assertEqual(shortest_prefix_match('*', ''), 0)
        self.assertEqual(shortest_prefix_match('a*', 'a'), 1)
        self.assertEqual(shortest_prefix_match('*b', 'aaab'), 4)
        self.assertEqual(shortest_prefix_match('**b', 'ab'), 2)
        self.assertEqual(shortest_prefix_match('{ab,cd}', 'cdx'), 2)
        self.assertEqual(shortest_prefix_match('{a,ab}c', 'abc'), 3)
        self.assertEqual(shortest_prefix_match('{*,a}b', 'ab'), 2)
        self.assertEqual(shortest_prefix_match('{,a}b', 'ab'), 2)
        self.assertEqual(shortest_prefix_match('{}', 'ab'), 0)
        self.assertEqual(shortest_prefix_match(r'{a,\{b}c', '{bcd'), 3)
        self.assertEqual(shortest_prefix_match(r'{\{a,b}', '{a'), 2)
        self.assertEqual(shortest_prefix_match('a?c', 'abcd'), 3)
        self.assertEqual(shortest_prefix_match(r'a\*b', 'a*bc'), 3)
        self.assertEqual(shortest_prefix_match('a', ''), -1)
        self.assertEqual(shortest_prefix_match('abc', 'ab'), -1)


class TestErrors(unittest.TestCase):
    def assertValueError(self, pattern, text='ab'):
        with self.assertRaises(ValueError):
            shortest_prefix_match(pattern, text)

    def test_errors(self):
        self.assertValueError('a\\')
        self.assertValueError('{a,b')
        self.assertValueError('a}b')
        self.assertValueError('{a,{b}c')
        self.assertValueError('{a{b}')


class TestEdge(unittest.TestCase):
    def test_empty_pattern(self):
        self.assertEqual(shortest_prefix_match('', 'abc'), 0)

    def test_star_zero(self):
        # '*' matches empty prefix
        self.assertEqual(shortest_prefix_match('a*b', 'aXXb'), 4)

    def test_question_requires_char(self):
        self.assertEqual(shortest_prefix_match('?', 'x'), 1)
        self.assertEqual(shortest_prefix_match('?', ''), -1)

    def test_no_match_returns_minus_one(self):
        self.assertEqual(shortest_prefix_match('z', 'abc'), -1)
        self.assertEqual(shortest_prefix_match('a?c', 'ac'), -1)

    def test_escaped_backslash(self):
        # '\\' matches a literal backslash
        self.assertEqual(shortest_prefix_match('a\\\\b', 'a\\b'), 3)

    def test_escaped_comma_in_group(self):
        self.assertEqual(shortest_prefix_match('{a\\,b,c}', 'a,b'), 3)

    def test_min_prefix_with_star_choice(self):
        # 'a*a' should match shortest: 'aa' is length 2? text 'aXXa'
        self.assertEqual(shortest_prefix_match('a*a', 'aXXa'), 4)
        self.assertEqual(shortest_prefix_match('a*a', 'aa'), 2)

    def test_group_with_star_alternative(self):
        self.assertEqual(shortest_prefix_match('{a*,ab}', 'abbb'), 1)


if __name__ == '__main__':
    unittest.main()
