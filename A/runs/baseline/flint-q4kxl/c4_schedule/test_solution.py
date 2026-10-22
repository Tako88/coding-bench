import random
import time
from itertools import combinations

from solution import best_schedule


def brute_force(intervals):
    n = len(intervals)
    best_key = None
    best_sol = (0, [])
    for mask in range(1 << n):
        sel = [intervals[i] for i in range(n) if (mask >> i) & 1]
        ok = True
        srt = sorted(sel)
        for a, b in zip(srt, srt[1:]):
            if a[1] > b[0]:
                ok = False
                break
        if not ok:
            continue
        profit = sum(t[2] for t in sel)
        key = (-profit, len(sel), [tuple(t) for t in sorted(sel)])
        if best_key is None or key < best_key:
            best_key = key
            best_sol = (profit, [tuple(t) for t in sorted(sel)])
    return best_sol


def check(intervals, expected):
    got = best_schedule(intervals)
    assert got == expected, f"intervals={intervals}\n expected={expected}\n got={got}"


def test_examples():
    check([], (0, []))
    check([(0, 3, 5)], (5, [(0, 3, 5)]))
    check([(0, 5, 3), (5, 10, 4)], (7, [(0, 5, 3), (5, 10, 4)]))
    check([(0, 5, 4), (5, 10, 4), (0, 10, 7)], (8, [(0, 5, 4), (5, 10, 4)]))
    check([(0, 10, 10), (1, 2, 1)], (10, [(0, 10, 10)]))
    check([(8, 10, 2), (5, 6, 2)], (4, [(5, 6, 2), (8, 10, 2)]))
    check(
        [(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)],
        (10, [(0, 2, 5), (2, 8, 5)]),
    )
    check([(0, 5, 5), (5, 10, 5), (0, 10, 10)], (10, [(0, 10, 10)]))
    check([(0, 1, 5), (1, 2, 5), (0, 2, 5)], (10, [(0, 1, 5), (1, 2, 5)]))
    check([(0, 2, 10), (1, 3, 1), (2, 4, 10)], (20, [(0, 2, 10), (2, 4, 10)]))
    check(
        [(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)],
        (2, [(0, 1, 1), (1, 2, 1)]),
    )


def test_random_against_brute_force():
    rng = random.Random(12345)
    for _ in range(400):
        n = rng.randint(0, 9)
        intervals = []
        for _ in range(n):
            start = rng.randint(0, 12)
            end = start + rng.randint(1, 6)
            profit = rng.randint(1, 6)
            intervals.append((start, end, profit))
        expected = brute_force(intervals)
        got = best_schedule(intervals)
        assert got == expected, f"intervals={intervals}\n expected={expected}\n got={got}"


def test_performance():
    n = 200000
    intervals = []
    for i in range(n):
        start = (i * 7) % 100000
        end = start + 2 + (i % 5)
        intervals.append((start, end, 1 + (i % 9)))
    t0 = time.time()
    result = best_schedule(intervals)
    dt = time.time() - t0
    assert isinstance(result, tuple) and isinstance(result[0], int)
    assert isinstance(result[1], list)
    print(f"performance run took {dt:.3f}s")
    assert dt < 3.0


if __name__ == "__main__":
    test_examples()
    test_random_against_brute_force()
    test_performance()
    print("ALL TESTS PASSED")
