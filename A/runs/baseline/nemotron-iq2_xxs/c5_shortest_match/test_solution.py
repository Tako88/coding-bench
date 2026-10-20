from solution import shortest_prefix_match


def check(pattern, text, expected):
    if isinstance(expected, int):
        got = shortest_prefix_match(pattern, text)
        assert got == expected, (
            f"shortest_prefix_match({pattern!r}, {text!r}) = {got!r}, "
            f"expected {expected!r}"
        )
    else:
        try:
            shortest_prefix_match(pattern, text)
        except ValueError:
            return
        except Exception as e:
            raise AssertionError(
                f"shortest_prefix_match({pattern!r}, {text!r}) raised {type(e).__name__}, "
                f"expected ValueError"
            )
        raise AssertionError(
            f"shortest_prefix_match({pattern!r}, {text!r}) did not raise, expected ValueError"
        )


# ---- Examples from TASK.md ----
check('abc', 'abcdef', 3)
check('a*c', 'abcde', 3)
check('*', 'abc', 0)
check('*', '', 0)
check('a*', 'a', 1)
check('*b', 'aaab', 4)
check('**b', 'ab', 2)
check('{ab,cd}', 'cdx', 2)
check('{a,ab}c', 'abc', 3)
check('{*,a}b', 'ab', 2)
check('{,a}b', 'ab', 2)
check('{}', 'ab', 0)
check('{a,\\{b}c', '{bcd', 3)
check('{\\{a,b}', '{a', 2)
check('a?c', 'abcd', 3)
check('a\\*b', 'a*bc', 3)
check('a', '', -1)
check('abc', 'ab', -1)

# ---- Error cases ----
check('a\\', 'a', ValueError)
check('{a,b', 'ab', ValueError)
check('a}b', 'ab', ValueError)
check('{a,{b}c', 'abc', ValueError)
check('{a{b}', 'a{b', ValueError)

# ---- Additional edge cases ----
check('', 'abc', 0)          # empty pattern matches empty prefix
check('', '', 0)
check('a*', 'abc', 1)        # star matches empty -> smallest L=1
check('*a', 'ba', 2)
check('*a', 'a', 1)
check('a*b', 'ab', 2)
check('a*b', 'acb', 3)       # a + *('c') + b
check('?', 'x', 1)
check('?', '', -1)
check('??', 'ab', 2)
check('{a,b}', 'b', 1)
check('{a,b}', 'c', -1)
check('\\{', '{', 1)         # escaped brace
check('\\}', '}', 1)
check('\\,', ',', 1)         # escaped comma
check('\\\\', '\\', 1)       # escaped backslash
check('a\\*b', 'a*b', 3)     # literal asterisk
check('{*,a}', '', 0)        # star alternative matches empty
check('{*,a}', 'a', 0)       # star alternative matches empty -> L=0
check('{*,a}', 'x', 0)       # star alternative matches empty -> L=0
check('{a,b}c', 'ac', 2)
check('{a,b}c', 'bc', 2)
check('*?', 'x', 1)          # star empty, then '?'
check('*?', '', -1)
check('a*', 'b', -1)         # requires 'a'
check('ab', 'abb', 2)        # exact two chars
check('a\\{b', 'a{b', 3)     # literal brace then b
check('{a,{b}', '{b', ValueError)  # unescaped brace inside group

# ---- Performance: many stars, long text ----
pattern = '*'.join(['x'] * 20) + 'z'  # 20 stars
text = 'a' * 4000
got = shortest_prefix_match(pattern, text)
assert got == -1, got

# Performance: long text that matches via stars
pattern2 = '*' * 20 + 'z'
text2 = 'a' * 4000 + 'z'
got2 = shortest_prefix_match(pattern2, text2)
assert got2 == 4001, got2

print("All tests passed.")
