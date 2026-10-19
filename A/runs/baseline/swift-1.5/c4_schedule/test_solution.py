"""Tests for solution.best_schedule.

Covers:
  * every example from TASK.md,
  * extra edge cases (duplicates, touching, identical intervals, empty),
  * randomized cross-checks against an exhaustive brute force,
  * a few structured tie-heavy cases,
  * a performance test with 200,000 intervals (must finish quickly).
"""

import random
import time

from solution import best_schedule


EXAMPLES = [
    ([], (0, [])),
    ([(0, 3, 5)], (5, [(0, 3, 5)])),
    ([(0, 5, 3), (5, 10, 4)], (7, [(0, 5, 3), (5, 10, 4)])),
    ([(0, 5, 4), (5, 10, 4), (0, 10, 7)], (8, [(0, 5, 4), (5, 10, 4)])),
    ([(0, 10, 10), (1, 2, 1)], (10, [(0, 10, 10)])),
    ([(8, 10, 2), (5, 6, 2)], (4, [(5, 6, 2), (8, 10, 2)])),
    ([(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)], (10, [(0, 2, 5), (2, 8, 5)])),
    ([(0, 5, 5), (5, 10, 5), (0, 10, 10)], (10, [(0, 10, 10)])),
    ([(0, 1, 5), (1, 2, 5), (0, 2, 5)], (10, [(0, 1, 5), (1, 2, 5)])),
    ([(0, 2, 10), (1, 3, 1), (2, 4, 10)], (20, [(0, 2, 10), (2, 4, 10)])),
    ([(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)], (2, [(0, 1, 1), (1, 2, 1)])),
]

EXTRA_CASES = [
    # two identical intervals overlap: at most one can be chosen
    ([(3, 4, 2), (3, 4, 2)], (2, [(3, 4, 2)])),
    # same start, all overlap; smallest (start, end, profit) wins
    ([(0, 1, 1), (0, 2, 1), (0, 3, 1)], (1, [(0, 1, 1)])),
    # duplicate first interval; chain of two
    ([(0, 2, 3), (0, 2, 3), (2, 4, 3)], (6, [(0, 2, 3), (2, 4, 3)])),
    # one interval beats two small ones on profit
    ([(0, 1, 1), (1, 2, 1), (0, 2, 5)], (5, [(0, 2, 5)])),
    # same geometry, different profits: higher profit wins, same triple order
    ([(0, 1, 1), (0, 1, 2)], (2, [(0, 1, 2)])),
    # two optimal (profit, count) sets; lexicographic order decides
    ([(0, 4, 3), (2, 6, 3), (4, 7, 3), (6, 8, 3)], (6, [(0, 4, 3), (4, 7, 3)])),
    # all intervals overlap pairwise
    ([(1, 5, 4), (2, 6, 9), (3, 7, 2)], (9, [(2, 6, 9)])),
    # touching intervals are compatible
    ([(0, 1, 1), (1, 2, 2), (2, 3, 3)], (6, [(0, 1, 1), (1, 2, 2), (2, 3, 3)])),
]


def brute(intervals):
    """Exhaustive reference implementation for small inputs.

    Enumerates every subset, keeps the non-overlapping ones, and picks the
    best by (profit desc, count asc, sorted triple list asc).
    """
    n = len(intervals)
    conflict = [0] * n
    for i in range(n):
        si, ei, _ = intervals[i]
        c = 0
        for j in range(n):
            if i != j:
                sj, ej, _ = intervals[j]
                if si < ej and sj < ei:
                    c |= 1 << j
        conflict[i] = c
    best_key = None
    for mask in range(1 << n):
        valid = True
        for i in range(n):
            if ((mask >> i) & 1) and (conflict[i] & mask):
                valid = False
                break
        if not valid:
            continue
        chosen = [intervals[i] for i in range(n) if (mask >> i) & 1]
        profit = sum(p for _, _, p in chosen)
        key = (-profit, len(chosen), sorted(chosen))
        if best_key is None or key < best_key:
            best_key = key
    if best_key is None:
        return (0, [])
    return (-best_key[0], best_key[2])


def run_examples():
    for ivs, expected in EXAMPLES:
        got = best_schedule(ivs)
        assert got == expected, (ivs, got, expected)
    for ivs, expected in EXTRA_CASES:
        got = best_schedule(ivs)
        assert got == expected, (ivs, got, expected)
        assert got == brute(ivs), (ivs, got, brute(ivs))
    print("examples + extra cases: OK")


def run_random():
    rng = random.Random(12345)
    trials = 500
    for t in range(trials):
        n = rng.randint(0, 12)
        tie_heavy = rng.random() < 0.3
        ivs = []
        for _ in range(n):
            s = rng.randint(0, 10)
            e = rng.randint(s + 1, min(s + 5, 14))
            p = rng.randint(1, 2) if tie_heavy else rng.randint(1, 6)
            ivs.append((s, e, p))
        got = best_schedule(ivs)
        exp = brute(ivs)
        assert got == exp, (t, ivs, got, exp)
    print("random vs brute (%d trials): OK" % trials)


def run_structured():
    # long chain of unit intervals
    ivs = [(i, i + 1, 1) for i in range(500)]
    assert best_schedule(ivs) == (500, ivs)
    # chain (500 intervals) vs one big interval (profit 500): count tie-break
    ivs = [(i, i + 1, 1) for i in range(500)] + [(0, 500, 500)]
    assert best_schedule(ivs) == (500, [(0, 500, 500)])
    # all identical: only one can be chosen
    ivs = [(0, 10, 1)] * 100
    assert best_schedule(ivs) == (1, [(0, 10, 1)])
    # profit tie, count tie, lex order: first element decides
    ivs = [(0, 2, 5), (1, 3, 5), (2, 4, 5), (3, 5, 5)]
    assert best_schedule(ivs) == (10, [(0, 2, 5), (2, 4, 5)])
    print("structured: OK")


def check_result(total, chosen):
    """Sanity checks on any returned result."""
    assert isinstance(total, int)
    assert chosen == sorted(chosen)
    assert total == sum(p for _, _, p in chosen)
    for a in range(1, len(chosen)):
        assert chosen[a][0] >= chosen[a - 1][1], (chosen[a - 1], chosen[a])


def run_perf():
    rng = random.Random(7)
    n = 200000
    ivs = []
    for _ in range(n):
        s = rng.randint(0, 100000)
        e = s + rng.randint(1, 20)
        p = rng.randint(1, 100)
        ivs.append((s, e, p))
    t0 = time.time()
    total, chosen = best_schedule(ivs)
    dt = time.time() - t0
    check_result(total, chosen)

    # adversarial: all 200k intervals identical
    ivs2 = [(0, 10, 1)] * 200000
    t0 = time.time()
    res2 = best_schedule(ivs2)
    dt2 = time.time() - t0
    assert res2 == (1, [(0, 10, 1)])

    # worst-ish case for the DP: dense overlapping chain
    ivs3 = [(i, i + 3, i % 7 + 1) for i in range(200000)]
    t0 = time.time()
    res3 = best_schedule(ivs3)
    dt3 = time.time() - t0
    check_result(res3[0], res3[1])

    print("perf: OK (random %.2fs, identical %.2fs, dense %.2fs)" % (dt, dt2, dt3))
    assert max(dt, dt2, dt3) < 3.0


if __name__ == "__main__":
    run_examples()
    run_random()
    run_structured()
    run_perf()
    print("ALL TESTS PASSED")
