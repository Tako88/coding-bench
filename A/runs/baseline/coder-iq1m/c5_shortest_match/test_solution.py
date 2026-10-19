"""Tests for solution.py (shortest_prefix_match).

Backslashes in patterns are written with BS = chr(92) so that this file says
exactly what TASK.md says ("a backslash in this file is one backslash
character").
"""

import importlib.util
import itertools
import random
import time

BS = chr(92)


def load_solution():
    spec = importlib.util.spec_from_file_location(
        "solution", __file__.replace("test_solution.py", "solution.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------
# Independent brute-force oracle (used only for small inputs in tests).
# It reuses the parser from solution.py, but implements matching by walking
# the element list backwards over sets of text positions.
# --------------------------------------------------------------------------

def oracle(mod, pattern, text):
    try:
        elements, _ = mod._parse_seq(pattern, 0, False)
    except ValueError:
        raise

    def match_seq(seq, ends):
        """Set of positions p such that seq matches text[p:q] for some q in ends."""
        res = set(ends)
        for el in reversed(seq):
            res = step(el, res)
        return res

    def step(el, ends):
        kind = el[0]
        if kind == 'lit':
            c = el[1]
            return {p for p in range(len(text) + 1)
                    if p + 1 in ends and p < len(text) and text[p] == c}
        if kind == 'any':
            return {p for p in range(len(text) + 1) if p + 1 in ends}
        if kind == 'star':
            out = set()
            ok_from = False
            for p in range(len(text), -1, -1):
                if p in ends:
                    ok_from = True
                if ok_from:
                    out.add(p)
            return out
        if kind == 'group':
            out = set()
            for alt in el[1]:
                out |= match_seq(alt, ends)
            return out
        raise AssertionError(kind)

    for L in range(len(text) + 1):
        if 0 in match_seq(elements, {L}):
            return L
    return -1


def check(mod, pattern, text, expected):
    got = mod.shortest_prefix_match(pattern, text)
    assert got == expected, "pattern=%r text=%r got=%r expected=%r" % (
        pattern, text, got, expected)


def check_error(mod, pattern, text=None):
    try:
        mod.shortest_prefix_match(pattern, text if text is not None else '')
    except ValueError:
        return
    raise AssertionError("pattern=%r should raise ValueError" % (pattern,))


def check_against_oracle(mod, pattern, text):
    got = mod.shortest_prefix_match(pattern, text)
    exp = oracle(mod, pattern, text)
    assert got == exp, "pattern=%r text=%r got=%r oracle=%r" % (pattern, text, got, exp)


def main():
    mod = load_solution()

    # ---------------- examples from TASK.md ----------------
    examples = [
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
        ('{a,' + BS + '{b}c', '{bcd', 3),
        ('{' + BS + '{a,b}', '{a', 2),
        ('a?c', 'abcd', 3),
        ('a' + BS + '*b', 'a*bc', 3),
        ('a', '', -1),
        ('abc', 'ab', -1),
    ]
    for pattern, text, expected in examples:
        check(mod, pattern, text, expected)
        print("ok   %r %r -> %d" % (pattern, text, expected))

    for pattern in ['a' + BS, '{a,b', 'a}b', '{a,' + '{b}c', '{a{b}']:
        check_error(mod, pattern)
        check_error(mod, pattern, 'ab')
        print("ok   %r -> ValueError" % pattern)

    # ---------------- extra edge cases ----------------
    edge = [
        ('', '', 0),
        ('', 'xyz', 0),
        ('?', '', -1),
        ('?', 'x', 1),
        ('??', 'x', -1),
        ('??', 'xy', 2),
        ('?', '\u00e9', 1),
        ('?', '\U0001f4b1', 1),
        ('*', 'abcdefgh', 0),
        ('**', '', 0),
        ('***', '', 0),
        ('a*', 'ba', -1),
        ('a*', '', -1),
        ('a*', 'abc', 1),
        ('*a', 'ba', 2),
        ('a*b*c', 'abc', 3),
        ('a*b*c', 'aXbYc', 5),
        ('a*b*c', 'abcX', 3),
        ('*x*', 'x', 1),
        ('*x*', 'zzxzz', 3),
        ('{a}', 'abc', 1),
        ('{a,b}', 'b', 1),
        ('{a,b}', 'c', -1),
        ('{,}', '', 0),
        ('{,,}', 'zz', 0),
        ('{*,*}', '', 0),
        ('{a*,b}', 'abz', 1),
        ('{a*,b}', 'bz', 1),
        ('{a?,b}x', 'abx', 3),
        ('{ab,}', 'ab', 0),
        ('{ab,}', 'zz', 0),
        ('a{b,c}d', 'acd', 3),
        ('{a,b}{c,d}', 'bd', 2),
        ('{a,b}*', 'azz', 1),
        ('{a,b}*', 'a', 1),
        ('{a,ab}*', 'ab', 1),
        ('{ab,a}b', 'ab', 2),
        ('a*a*a', 'aaa', 3),
        ('*a', 'aa', 1),
        ('a*a', 'aaaa', 2),
        ('?', '\u20acabc', 1),
    ]
    for pattern, text, expected in edge:
        check(mod, pattern, text, expected)

    # literals written with escapes
    lit = [
        (BS + BS, BS, 1),
        ('x' + BS + BS + 'y', 'x' + BS + 'y', 3),
        (BS + '{', '{', 1),
        (BS + '}', '}', 1),
        (BS + '*', '*', 1),
        (BS + '?', '?', 1),
        (BS + ',', ',', 1),
        (BS + 'a', 'a', 1),
        ('{a,' + BS + '}b}', '}b', 2),
        ('{a,' + BS + ',}', ',', 1),
        ('{' + BS + '{,b}', '{{b'[:1], 1),
        (BS + '*?', '*?', 2),
        ('?*x', '?x', 2),
    ]
    for pattern, text, expected in lit:
        check(mod, pattern, text, expected)
        print("ok   %r %r -> %d" % (pattern, text, expected))

    # a comma outside a group is an ordinary character
    for pattern, text, expected in [(',', ',', 1), ('a,b', 'a,b', 3), (BS + ',', ',z', 1), (',', 'a', -1)]:
        check(mod, pattern, text, expected)

    # escaped braces need no closing brace
    check(mod, BS + '{', 'a{b', -1)
    check(mod, BS + '}', '{', -1)

    # more malformed patterns
    bad = ['{', '{a', '{a,b}}', '}', 'a}b', '{{a}a}', '{a{b}', '{a,{b}c',
           'x' + BS, BS + '?x' + BS, '{a,\\' + 'b', '{' + BS]
    for pattern in bad:
        check_error(mod, pattern)
        print("ok   %r -> ValueError" % pattern)

    # random cross-check against the brute-force oracle
    tokens = ['a', 'b', '*', '?', '{a,b}', '{a,}', '{}', '{*,a}', '{,a}',
              '{ab,c*}', BS + '{', BS + ',', BS + '*', 'ab', '{a,b}*', 'a*b']
    texts = ['', 'a', 'b', 'ab', 'ba', 'aab', 'aba', 'bbab', 'abab', 'baaa']
    random.seed(12345)
    for _ in range(4000):
        k = random.randint(1, 4)
        pattern = ''.join(random.choice(tokens) for _ in range(k))
        text = random.choice(texts)
        check_against_oracle(mod, pattern, text)
    print("ok   4000 random patterns match the brute-force oracle")

    for _ in range(600):
        pattern = random.choice([
            'a?b*c', '{a,{b}', '{a,' + BS + ',b}x', '{' + BS + '{a,*}?',
            BS, '}', '*{,a}b{c,d}', '{' + BS + '*a}b?'])
        try:
            check_against_oracle(mod, pattern, random.choice(texts))
        except ValueError:
            pass
    print("ok   random mixed patterns consistent")

    # ---------------- performance ----------------
    big = 'a' * 4000
    cases = [
        ('*a' * 20, big, 20),
        ('a*' * 20 + 'a', big, 21),
        ('*' * 20 + 'a' * 20, big, 20),
        ('*' * 20 + '{a,b}' * 5, big, 5),
        ('{a*,b}' * 10 + 'c', big, -1),
        ('*a' * 19 + 'b', big, -1),
        ('?' + '*' * 20 + '?' * 3, big, 4),
        ('{a*,b*,c*}' * 6 + 'x', big + 'x', 4001),
        ('{a*,b*,c*}' * 6 + 'x', big, -1),
        ('*a' * 20 + 'b', 'a' * 3999 + 'b', 4000),
        ('?' .join(['*' + 'a' * 10] * 15), big, 164),
        ('{,' + 'a' * 20 + '}*', big, 0),
    ]
    for pattern, text, expected in cases:
        t0 = time.time()
        got = mod.shortest_prefix_match(pattern, text)
        dt = time.time() - t0
        assert got == expected, (pattern, got, expected)
        assert dt < 8.0, "too slow: %.2fs" % dt
        print("perf ok  %-30s n=%d  %.3fs" % (pattern[:30], len(text), dt))

    print("ALL TESTS PASSED")


if __name__ == '__main__':
    main()
