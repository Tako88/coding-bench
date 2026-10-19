"""Tests for solution.best_schedule: examples, edge cases, brute-force
cross-checks on small random inputs, and performance checks."""

import random
import time

from solution import best_schedule

# --- examples from TASK.md -------------------------------------------------

EXAMPLES = [
    ([], (0, [])),
    ([(0, 3, 5)], (5, [(0, 3, 5)])),
    ([(0, 5, 3), (5, 10, 4)], (7, [(0, 5, 3), (5, 10, 4)])),
    ([(0, 5, 4), (5, 10, 4), (0, 10, 7)], (8, [(0, 5, 4), (5, 10, 4)])),
    ([[0, 10, 10], [1, 2, 1]], (10, [(0, 10, 10)])),
    ([(8, 10, 2), (5, 6, 2)], (4, [(5, 6, 2), (8, 10, 2)])),
    ([(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)], (10, [(0, 2, 5), (2, 8, 5)])),
    ([(0, 5, 5), (5, 10, 5), (0, 10, 10)], (10, [(0, 10, 10)])),
    ([(0, 1, 5), (1, 2, 5), (0, 2, 5)], (10, [(0, 1, 5), (1, 2, 5)])),
    ([(0, 2, 10), (1, 3, 1), (2, 4, 10)], (20, [(0, 2, 10), (2, 4, 10)])),
    ([(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)], (2, [(0, 1, 1), (1, 2, 1)])),
]

# --- hand-made edge cases ---------------------------------------------------

EDGE_CASES = [
    # profit tie, count tie -> lex-smallest triple wins (earlier start)
    ([(5, 6, 3), (0, 10, 3)], (3, [(0, 10, 3)])),
    # identical intervals overlap: at most one
    ([(0, 1, 5), (0, 1, 5)], (5, [(0, 1, 5)])),
    # count rule: 1 interval beats 2 of the same profit
    ([(0, 2, 2), (0, 1, 1), (1, 2, 1)], (2, [(0, 2, 2)])),
    # profit rule: 2 intervals (4) beat 1 (3)
    ([(0, 2, 3), (0, 1, 2), (1, 2, 2)], (4, [(0, 1, 2), (1, 2, 2)])),
    # must skip the (0,3,1) interval: its extension cannot reach total 12
    ([(0, 3, 1), (0, 3, 2), (3, 4, 10)], (12, [(0, 3, 2), (3, 4, 10)])),
    # lex rule with three equal (profit,count) solutions; the one with the
    # smaller second element must win:
    #   {(0,2,2),(2,4,2)} < {(0,2,2),(3,5,2)} < {(0,3,2),(3,5,2)}
    ([(0, 3, 2), (3, 5, 2), (0, 2, 2), (2, 4, 2)],
     (4, [(0, 2, 2), (2, 4, 2)])),
    # identical leading triple realized at two indices
    ([(0, 1, 2), (0, 1, 2), (1, 2, 1), (1, 2, 2)],
     (4, [(0, 1, 2), (1, 2, 2)])),
    # greedy must skip a feasible-looking early interval whose continuation
    # needs too many intervals (count tie-break), then pick the big one
    ([(0, 5, 5), (5, 10, 5), (0, 10, 10)], (10, [(0, 10, 10)])),
    # all overlapping: pick the max-profit interval
    ([(2, 4, 7), (1, 9, 7), (3, 5, 8)], (8, [(3, 5, 8)])),
    # touching chains
    ([(0, 1, 1), (1, 2, 1), (2, 3, 1)], (3, [(0, 1, 1), (1, 2, 1), (2, 3, 1)])),
    # single-interval tie: (2,9,5) < (3,4,5) by start, despite longer end
    ([(0, 4, 3), (3, 4, 5), (2, 7, 3), (1, 6, 3), (2, 9, 5), (2, 9, 3)],
     (5, [(2, 9, 5)])),
]


def test_examples():
    for ivs, expected in EXAMPLES:
        got = best_schedule(ivs)
        assert got == expected, (ivs, got, expected)


def test_edge_cases():
    for ivs, expected in EDGE_CASES:
        got = best_schedule(ivs)
        assert got == expected, (ivs, got, expected)


# --- brute force cross-check ------------------------------------------------

def _non_overlapping(sel):
    for x in range(len(sel)):
        for y in range(x + 1, len(sel)):
            a, b = sel[x], sel[y]
            if not (a[1] <= b[0] or b[1] <= a[0]):
                return False
    return True


def _prefers(a, b):
    """True if candidate a (profit, count, lst) beats candidate b:
    larger profit, then smaller count, then smaller lex list."""
    if a[0] != b[0]:
        return a[0] > b[0]
    if a[1] != b[1]:
        return a[1] < b[1]
    return a[2] < b[2]


def brute(intervals):
    n = len(intervals)
    best = None  # (profit, count, sorted list)
    for mask in range(1 << n):
        sel = [intervals[i] for i in range(n) if (mask >> i) & 1]
        if not _non_overlapping(sel):
            continue
        cand = (sum(t[2] for t in sel), len(sel), sorted(sel))
        if best is None or _prefers(cand, best):
            best = cand
    if best is None:
        return (0, [])
    return (best[0], best[2])


def test_random_sparse():
    rng = random.Random(12345)
    for _ in range(400):
        n = rng.randint(0, 11)
        ivs = []
        for _ in range(n):
            a = rng.randint(0, 8)
            b = rng.randint(0, 8)
            if a >= b:
                a, b = b, a + 1
            ivs.append((a, b, rng.randint(1, 5)))
        got = best_schedule(ivs)
        exp = brute(ivs)
        assert got == exp, (ivs, got, exp)


def test_random_dense():
    # small coordinate space -> many overlaps and ties
    rng = random.Random(777)
    for _ in range(400):
        n = rng.randint(0, 11)
        ivs = []
        for _ in range(n):
            a = rng.randint(0, 3)
            b = a + rng.randint(1, 3)
            ivs.append((a, b, rng.randint(1, 3)))
        got = best_schedule(ivs)
        exp = brute(ivs)
        assert got == exp, (ivs, got, exp)


def test_random_duplicates():
    # heavy duplicates to exercise identical-interval handling
    rng = random.Random(2024)
    for _ in range(200):
        n = rng.randint(0, 10)
        ivs = []
        for _ in range(n):
            a = rng.randint(0, 2)
            b = a + rng.randint(1, 2)
            ivs.append((a, b, rng.randint(1, 2)))
        got = best_schedule(ivs)
        exp = brute(ivs)
        assert got == exp, (ivs, got, exp)


# --- performance -------------------------------------------------------------

def _check_result(total, chosen):
    assert isinstance(total, int)
    assert all(chosen[i][1] <= chosen[i + 1][0]
               for i in range(len(chosen) - 1)), "overlap in result"
    assert chosen == sorted(chosen), "result not sorted"
    assert sum(t[2] for t in chosen) == total, "profit mismatch"


def test_performance_random():
    rng = random.Random(42)
    n = 200_000
    ivs = []
    for _ in range(n):
        a = rng.randint(0, 10_000)
        b = a + rng.randint(1, 500)
        ivs.append((a, b, rng.randint(1, 100)))
    t0 = time.time()
    total, chosen = best_schedule(ivs)
    dt = time.time() - t0
    _check_result(total, chosen)
    print("performance (200k random): %.2fs, profit=%d, chosen=%d"
          % (dt, total, len(chosen)))
    assert dt < 3.0, "too slow: %.2fs" % dt


def test_performance_chain():
    # 200k mutually compatible intervals: all must be chosen
    n = 200_000
    ivs = [(i, i + 1, 1) for i in range(n)]
    t0 = time.time()
    total, chosen = best_schedule(ivs)
    dt = time.time() - t0
    assert total == n and len(chosen) == n
    print("performance (200k chain): %.2fs" % dt)
    assert dt < 3.0, "too slow: %.2fs" % dt


def test_performance_identical():
    ivs = [(0, 1, 1)] * 200_000
    t0 = time.time()
    got = best_schedule(ivs)
    dt = time.time() - t0
    assert got == (1, [(0, 1, 1)])
    print("performance (200k identical): %.2fs" % dt)
    assert dt < 3.0, "too slow: %.2fs" % dt


def test_performance_big_profits():
    rng = random.Random(9)
    n = 200_000
    ivs = []
    for _ in range(n):
        a = rng.randint(0, 10_000)
        b = a + rng.randint(1, 500)
        ivs.append((a, b, rng.randint(10 ** 15, 10 ** 18)))
    t0 = time.time()
    total, chosen = best_schedule(ivs)
    dt = time.time() - t0
    _check_result(total, chosen)
    print("performance (200k big profits): %.2fs" % dt)
    assert dt < 3.0, "too slow: %.2fs" % dt


def main():
    test_examples()
    test_edge_cases()
    test_random_sparse()
    test_random_dense()
    test_random_duplicates()
    print("correctness tests passed")
    test_performance_random()
    test_performance_chain()
    test_performance_identical()
    test_performance_big_profits()
    print("All tests passed.")


if __name__ == "__main__":
    main()
