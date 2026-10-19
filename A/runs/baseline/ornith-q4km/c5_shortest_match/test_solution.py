import solution


def check(pat, text, expected):
    got = solution.shortest_prefix_match(pat, text)
    assert got == expected, f"{pat!r} vs {text!r}: expected {expected}, got {got}"


def check_error(pat):
    try:
        solution.shortest_prefix_match(pat, "ab")
    except ValueError:
        return
    raise AssertionError(f"expected ValueError for {pat!r}")


# ---- Examples from the spec ----
def test_examples():
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
    check(r'{a,\{b}c', '{bcd', 3)
    check(r'{\{a,b}', '{a', 2)
    check('a?c', 'abcd', 3)
    check(r'a\*b', 'a*bc', 3)


def test_errors():
    check_error('a\\')
    check_error('{a,b')
    check_error('a}b')
    check_error(r'{a,{b}c')
    check_error('{a{b}')


def test_no_match():
    check('a', '', -1)
    check('abc', 'ab', -1)
    check('a', 'b', -1)
    check('xyz', 'abcde', -1)


def test_edge_cases():
    # empty pattern matches empty prefix
    check('', 'abc', 0)
    check('', '', 0)
    # star matches empty
    check('**', 'abcd', 0)
    # group with empty alternative gives L=0
    check('{,}', 'ab', 0)
    check('{a,}', 'bc', 0)
    # literal comma/brace via escape
    check('a\\,b', 'axb', -1)
    check('a\\,b', 'a,b', 3)
    check('\\{', '{', 1)
    check('\\}', '}', 1)
    check('a\\}', 'a}', 2)
    # '?' must match exactly one
    check('a?c', 'ac', -1)
    check('a?c', 'abc', 3)
    # '*' smallest: earliest full match
    check('a*b', 'aaXbYY', 4)
    # group alternatives each being star-like
    check('{*a,*b}', 'xxa', 3)


def test_performance():
    import time
    text = 'a' * 4000
    pat = '*' * 20 + 'z'
    t0 = time.time()
    r = solution.shortest_prefix_match(pat, text)
    dt = time.time() - t0
    assert dt < 10, f"too slow: {dt:.2f}s"
    assert r == -1, r


if __name__ == '__main__':
    funcs = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    for f in funcs:
        f()
        print("ok:", f.__name__)
    print("ALL TESTS PASSED")
