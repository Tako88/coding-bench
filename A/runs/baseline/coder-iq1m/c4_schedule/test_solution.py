"""Self-tests for solution.best_schedule."""

import itertools
import random
import time

from solution import best_schedule


def brute(intervals):
    """Reference implementation: try every subset, apply the three rules literally."""
    ivs = [tuple(t) for t in intervals]
    n = len(ivs)
    best_key = None
    best_val = None
    for mask in range(1 << n):
        sel = []
        ok = True
        for a in range(n):
            if not (mask >> a) & 1:
                continue
            for b in range(a):
                if (mask >> b) & 1:
                    sa, ea = ivs[a][0], ivs[a][1]
                    sb, eb = ivs[b][0], ivs[b][1]
                    if not (ea <= sb or eb <= sa):
                        ok = False
                        break
            if not ok:
                break
            sel.append(ivs[a])
        if not ok:
            continue
        sel.sort()
        profit = sum(t[2] for t in sel)
        key = (-profit, len(sel), sel)
        if best_key is None or key < best_key:
            best_key = key
            best_val = (profit, sel)
    return best_val


def check(intervals):
    got_profit, got_chosen = best_schedule(intervals)
    exp_profit, exp_chosen = brute(intervals)
    assert got_profit == exp_profit, (intervals, got_profit, exp_profit)
    assert got_chosen == exp_chosen, (intervals, got_chosen, exp_chosen)

    # sanity: chosen must be valid, sorted, and consistent with the reported profit
    assert got_chosen == sorted(got_chosen)
    assert len(set(range(len(got_chosen)))) == len(got_chosen)
    assert sum(t[2] for t in got_chosen) == got_profit
    for a in range(len(got_chosen)):
        for b in range(a):
            ea, sb = got_chosen[a][1], got_chosen[b][0]
            eb, sa = got_chosen[b][1], got_chosen[a][0]
            assert ea <= sb or eb <= sa, (intervals, got_chosen)


def test_examples():
    cases = [
        ([], (0, [])),
        ([(0, 3, 5)], (5, [(0, 3, 5)])),
        ([(0, 5, 3), (5, 10, 4)], (7, [(0, 5, 3), (5, 10, 4)])),
        ([(0, 5, 4), (5, 10, 4), (0, 10, 7)], (8, [(0, 5, 4), (5, 10, 4)])),
        ([(0, 10, 10), (1, 2, 1)], (10, [(0, 10, 10)])),
        ([(8, 10, 2), (5, 6, 2)], (4, [(5, 6, 2), (8, 10, 2)])),
        ([(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)],
         (10, [(0, 2, 5), (2, 8, 5)])),
        ([(0, 5, 5), (5, 10, 5), (0, 10, 10)], (10, [(0, 10, 10)])),
        ([(0, 1, 5), (1, 2, 5), (0, 2, 5)], (10, [(0, 1, 5), (1, 2, 5)])),
        ([(0, 2, 10), (1, 3, 1), (2, 4, 10)], (20, [(0, 2, 10), (2, 4, 10)])),
        ([(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)],
         (2, [(0, 1, 1), (1, 2, 1)])),
    ]
    for intervals, expected in cases:
        got = best_schedule(intervals)
        assert got == expected, (intervals, got, expected)
        check(intervals)
    print("examples OK")


def test_random_small():
    """Compare against brute force over many small random instances (incl. duplicates)."""
    random.seed(12345)
    cases = 0
    for trial in range(400):
        n = random.randint(0, 9)
        span = random.choice([1, 3, 5, 8])
        pool = [(s, e, p)
                for s in range(span + 1)
                for e in range(s + 1, 2 * span + 1)
                for p in (1, 2, 5)]
        intervals = [random.choice(pool) for _ in range(n)]
        check(intervals)
        cases += 1
    print("random small vs brute OK (%d cases)" % cases)


def test_ties_and_edge_shapes():
    random.seed(999)
    # many identical intervals: at most one can be taken
    ivs = [(3, 7, 4)] * 12
    assert best_schedule(ivs) == (4, [(3, 7, 4)])

    # zero-profit-free chain of touching intervals
    ivs = [(i, i + 1, 1) for i in range(20)]
    assert best_schedule(ivs) == (20, ivs)

    # big interval vs many small ones with equal profit, count tie-break
    ivs = [(0, 4, 4), (0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 4, 1)]
    assert best_schedule(ivs) == (4, [(0, 4, 4)])

    # lexicographic tie: same profit, same count -> smallest triples win
    ivs = [(0, 9, 5), (0, 2, 5), (2, 9, 5)]
    assert best_schedule(ivs) == (10, [(0, 2, 5), (2, 9, 5)])
    ivs2 = [(2, 9, 5), (0, 9, 5), (0, 2, 5), (0, 9, 5)]
    assert best_schedule(ivs2) == (10, [(0, 2, 5), (2, 9, 5)])

    # huge coordinates, single interval
    assert best_schedule([(10 ** 15, 10 ** 15 + 7, 10 ** 12)]) == (10 ** 12,
                                                                  [(10 ** 15, 10 ** 15 + 7, 10 ** 12)])

    # unsorted input, duplicate triples
    ivs = [(5, 6, 2), (0, 1, 1), (5, 6, 2), (1, 5, 9), (0, 1, 1)]
    assert best_schedule(ivs) == (12, [(0, 1, 1), (1, 5, 9), (5, 6, 2)])
    print("edge shapes OK")


def test_performance():
    n = 200_000
    random.seed(7)
    intervals = []
    for _ in range(n):
        s = random.randrange(0, 2_000_000)
        e = s + random.randint(1, 5000)
        p = random.randint(1, 1000)
        intervals.append((s, e, p))
    t0 = time.time()
    profit, chosen = best_schedule(intervals)
    elapsed = time.time() - t0

    # validate the big answer without brute force
    assert chosen == sorted(chosen)
    assert sum(t[2] for t in chosen) == profit
    for a in range(1, len(chosen)):
        assert chosen[a - 1][1] <= chosen[a][0]
    assert elapsed < 3.0, "too slow: %.2fs" % elapsed
    print("performance OK: n=%d, profit=%d, chosen=%d, %.2fs"
          % (n, profit, len(chosen), elapsed))

    # structured worst cases: all identical / all disjoint
    t0 = time.time()
    best_schedule([(1, 2, 1)] * n)
    best_schedule([(i, i + 1, 1) for i in range(n)])
    best_schedule([(0, i + 1, i + 1) for i in range(n)])
    print("structured cases in %.2fs" % (time.time() - t0))


if __name__ == "__main__":
    test_examples()
    test_random_small()
    test_ties_and_edge_shapes()
    test_performance()
    print("ALL TESTS PASSED")
