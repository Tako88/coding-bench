"""Tests for solution.shortest_prefix_match.

Patterns are written as raw strings: a backslash in the source is one
literal backslash character, exactly as written in TASK.md.
"""
import random
import time

from solution import (
    _CHAR, _GROUP, _QMARK, _STAR,
    shortest_prefix_match,
)


failures = []


# ------------------------------------------------- differential fuzzing
# Independent, naive (exponential backtracking) reference matcher: for a
# parsed element list it returns the smallest L (or -1) exactly by
# definition.  Element shapes follow solution._parse: (_CHAR, ch),
# (_QMARK,), (_STAR,), (_GROUP, [alt, ...]).

def naive_best_L(elements, text):
    n = len(text)

    def flat_ends(alt, j):
        # set of p such that alt (simple elements only) eats text[j:p]
        pos = {j}
        for el in alt:
            kind = el[0]
            nxt = set()
            for p in pos:
                if kind == _CHAR:
                    if p < n and text[p] == el[1]:
                        nxt.add(p + 1)
                elif kind == _QMARK:
                    if p < n:
                        nxt.add(p + 1)
                else:  # _STAR
                    nxt.update(range(p, n + 1))
            pos = nxt
            if not pos:
                break
        return pos

    memo = {}

    def F(i, j):
        # set of p such that elements[i:] eats text[j:p] exactly
        key = (i, j)
        if key in memo:
            return memo[key]
        if i == len(elements):
            memo[key] = frozenset({j})
            return memo[key]
        el = elements[i]
        kind = el[0]
        if kind == _CHAR:
            res = F(i + 1, j + 1) if j < n and text[j] == el[1] else frozenset()
        elif kind == _QMARK:
            res = F(i + 1, j + 1) if j < n else frozenset()
        elif kind == _STAR:
            res = set()
            for k in range(j, n + 1):
                res |= F(i + 1, k)
            res = frozenset(res)
        else:  # _GROUP
            res = set()
            for alt in el[1]:
                for k in flat_ends(alt, j):
                    res |= F(i + 1, k)
            res = frozenset(res)
        memo[key] = res
        return res

    ends = F(0, 0) if elements else frozenset({0})
    return min(ends) if ends else -1


def run_fuzz():
    rng = random.Random(20240501)

    def gen_simple():
        r = rng.random()
        if r < 0.45:
            c = rng.choice('ab')
            return c, (_CHAR, c)
        if r < 0.62:
            c = rng.choice(['{', ',', '}', '?', '*', '\\', 'a'])
            return '\\' + c, (_CHAR, c)
        if r < 0.78:
            return '?', (_QMARK,)
        return '*', (_STAR,)

    def gen_group():
        alts = []
        for _ in range(rng.randint(1, 3)):
            s = []
            els = []
            for _ in range(rng.randint(0, 3)):
                tok, el = gen_simple()
                s.append(tok)
                els.append(el)
            alts.append(( ''.join(s), els))
        body = ','.join(s for s, _ in alts)
        return '{' + body + '}', (_GROUP, [els for _, els in alts])

    def gen_pattern():
        parts = []
        els = []
        for _ in range(rng.randint(0, 5)):
            if rng.random() < 0.3:
                s, el = gen_group()
            else:
                s, el = gen_simple()
            parts.append(s)
            els.append(el)
        return ''.join(parts), els

    for _ in range(1500):
        pattern, els = gen_pattern()
        text = ''.join(rng.choice('ab,{') for _ in range(rng.randint(0, 8)))
        expected = naive_best_L(els, text)
        try:
            got = shortest_prefix_match(pattern, text)
        except Exception as e:  # noqa: BLE001
            failures.append('fuzz %r/%r raised %r' % (pattern, text, e))
            continue
        if got != expected:
            failures.append('fuzz %r/%r: expected %r, got %r'
                            % (pattern, text, expected, got))

    # Robustness: on the pattern alphabet the function must either return
    # an int (well-formed pattern) or raise ValueError (malformed).
    alpha = 'ab?,\\{}'
    for _ in range(3000):
        s = ''.join(rng.choice(alpha) for _ in range(rng.randint(0, 12)))
        try:
            r = shortest_prefix_match(s, 'ab')
            if not isinstance(r, int):
                failures.append('fuzz raw %r: returned non-int %r'
                                % (s, r))
        except ValueError:
            pass
        except Exception as e:  # noqa: BLE001
            failures.append('fuzz raw %r: unexpected %r' % (s, e))


def expect(pattern, text, expected):
    try:
        got = shortest_prefix_match(pattern, text)
    except Exception as e:  # noqa: BLE001
        failures.append('%r/%r: expected %r, raised %r'
                        % (pattern, text, expected, e))
        return
    if not isinstance(got, int) or got != expected:
        failures.append('%r/%r: expected %r, got %r'
                        % (pattern, text, expected, got))


def expect_error(pattern, text):
    try:
        got = shortest_prefix_match(pattern, text)
    except ValueError:
        return
    except Exception as e:  # noqa: BLE001
        failures.append('%r/%r: expected ValueError, raised %r'
                        % (pattern, text, e))
        return
    failures.append('%r/%r: expected ValueError, got %r'
                    % (pattern, text, got))


# ---------------------------------------------------------------- examples
# All examples straight from TASK.md (patterns shown as written).
expect('abc', 'abcdef', 3)
expect('a*c', 'abcde', 3)
expect('*', 'abc', 0)
expect('*', '', 0)
expect('a*', 'a', 1)
expect('*b', 'aaab', 4)
expect('**b', 'ab', 2)
expect('{ab,cd}', 'cdx', 2)
expect('{a,ab}c', 'abc', 3)
expect('{*,a}b', 'ab', 2)
expect('{,a}b', 'ab', 2)
expect('{}', 'ab', 0)
expect(r'{a,\{b}c', '{bcd', 3)
expect(r'{\{a,b}', '{a', 2)
expect('a?c', 'abcd', 3)
expect(r'a\*b', 'a*bc', 3)
expect('a', '', -1)
expect('abc', 'ab', -1)

# Malformed patterns -> ValueError.
expect_error('a\\', 'a')
expect_error('{a,b', 'ab')
expect_error('a}b', 'ab')
expect_error('{a,{b}c', 'abc')
expect_error('{a{b}', 'a{b')

# ------------------------------------------------------------- more edges
# Empty pattern / empty text.
expect('', 'abc', 0)
expect('', '', 0)
expect('*', '', 0)

# Question marks.
expect('?', 'a', 1)
expect('?', '', -1)
expect('??', 'ab', 2)
expect('??', 'a', -1)
expect('a?', 'ab', 2)
expect('??*', 'abc', 2)
expect('*?', 'ab', 1)

# Stars: shortest prefix behavior, repeated stars, stars around literals.
expect('a*b', 'axxb', 4)
expect('a*b', 'a', -1)
expect('*a', 'aaa', 1)
expect('a*a', 'aa', 2)
expect('**', 'abc', 0)
expect('**', '', 0)
expect('a**b', 'ab', 2)
expect('*a*b*', 'xxaxb', 5)
expect('a*a*a*', 'a', -1)

# Escapes outside groups.
expect('\\\\', '\\', 1)
expect('\\\\', 'x', -1)
expect(r'a\,b', 'a,b', 3)
expect(r'a\,b', 'ab', -1)
expect(r'\?', '?', 1)
expect(r'\?', 'a', -1)
expect(r'a\\b', r'a\b', 3)
expect(r'\{', '{', 1)
expect(r'\{', 'x', -1)
expect(r'\}', '}', 1)
expect(r'\*', '*', 1)

# Plain ',' outside a group is an ordinary character.
expect('*,', 'x,', 2)
expect('*,', 'x*', -1)
expect('a,,b', 'a,,b', 4)

# Groups: alternative ordering, empty alternatives, trailing comma,
# stars inside groups, single-alternative groups.
expect('{a,}', 'a', 0)
expect('{a,}', '', 0)
expect('{,}', 'xyz', 0)
expect('{a,ab}', 'ab', 1)
expect('{ab,a}', 'ab', 1)
expect('{a,}', 'b', 0)
expect('{,a,b}', 'b', 0)
expect('{,a,b}', '', 0)
expect('{a}b', 'ab', 2)
expect('{a}b', 'a', -1)
expect_error('{a,b{', 'ab{')         # unescaped '{' inside an alternative
expect('{*,ab}c', 'xabc', 4)
expect('{a*,b}', 'abc', 1)
expect('{*a}', 'ba', 2)
expect('{,}', '', 0)
expect('{a\\,b}', 'a,b', 3)
expect('{a\\,b}', 'ab', -1)
expect('{a\\}b}', 'a}b', 3)
expect('{a\\}b}', 'ab', -1)
expect('{a\\}b}', 'a}b}c', 3)

# Escape of the closing brace inside a group.
expect(r'{a\}b}', 'a}b', 3)
expect(r'{a\}b}', 'a}b}c', 3)
expect(r'{a\}b}', 'ab', -1)

# Unicode: one code point per character.
expect('€*', '€x', 1)
expect('é?', 'é', -1)
expect('é?', 'éx', 2)
expect('€?', '', -1)
expect('*', 'αβγ', 0)
expect('α*β', 'αβγ', 2)

# Larger / worst-ish cases (still far under 10 seconds).
big_text = 'a' * 4000
expect('*' * 20, big_text, 0)
expect('a' * 20 + 'b', 'a' * 20 + 'b' + 'a' * 3979, 21)
expect('a' * 20, 'a' * 4000, 20)
expect('a' * 4000, 'a' * 4000, 4000)
expect('a' * 4001, 'a' * 4000, -1)
text2 = 'a' * 3999 + 'z'
expect('*' * 20 + 'z', text2, 4000)
expect('a' * 10 + 'z', 'a' * 10 + 'z' + 'a' * 3989, 11)
expect('a' * 10 + 'z', 'a' * 4000, -1)
mixed = ('ab' * 2000)
expect(('ab' + '*') * 20 + 'ab', mixed, 42)
expect(('a?' + 'b*') * 20, 'a' * 4000, -1)
expect(('a' + 'b' + '*') * 20 + 'a', 'ab' * 2000, 41)

# Timing sanity: a pattern heavy in stars and text of 4000 chars must be
# fast (spec limit is 10 s; we ask for a comfortable margin).
t0 = time.time()
for _ in range(20):
    expect('a' * 20 + '*' * 20 + 'b', 'a' * 1998 + 'b' + 'a' * 2001, 1999)
elapsed = time.time() - t0
if elapsed > 5:
    failures.append('timing: 20 calls took %.1fs (> 5s)' % elapsed)


run_fuzz()


def main():
    main_failures = len(failures)
    if main_failures:
        print('FAILED: %d test(s) failed' % main_failures)
        for f in failures:
            print('  ' + f)
        raise SystemExit(1)
    print('OK: all tests passed')


if __name__ == '__main__':
    main()
