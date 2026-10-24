import random
from solution import best_schedule


def brute(intervals):
    """Reference: enumerate all feasible subsets, pick by the 3-level rule."""
    n = len(intervals)
    best = None  # (profit, -count, sorted_triples)
    best_set = None
    for mask in range(1 << n):
        sel = [intervals[i] for i in range(n) if mask & (1 << i)]
        # feasibility: pairwise non-overlapping
        ok = True
        sel_sorted = sorted(sel)
        for a in range(len(sel_sorted) - 1):
            if sel_sorted[a][1] > sel_sorted[a + 1][0]:
                ok = False
                break
        if not ok:
            continue
        profit = sum(x[2] for x in sel_sorted)
        negcount = -len(sel_sorted)
        cand = (profit, negcount, sel_sorted)
        # We want max profit, then max -count (min count), then min list.
        if best is None or cand[0] > best[0] or (
            cand[0] == best[0] and cand[1] > best[1]
        ) or (
            cand[0] == best[0] and cand[1] == best[1] and cand[2] < best[2]
        ):
            best = cand
            best_set = sel_sorted
    if best_set is None:
        return (0, [])
    return (best[0], best_set)


def check(intervals):
    got = best_schedule(intervals)
    exp = brute(intervals)
    assert got == exp, f"MISMATCH\n  input={intervals}\n  got={got}\n  exp ={exp}"


def test_examples():
    cases = [
        [],
        [(0, 3, 5)],
        [(0, 5, 3), (5, 10, 4)],
        [(0, 5, 4), (5, 10, 4), (0, 10, 7)],
        [(0, 10, 10), (1, 2, 1)],
        [(8, 10, 2), (5, 6, 2)],
        [(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)],
        [(0, 5, 5), (5, 10, 5), (0, 10, 10)],
        [(0, 1, 5), (1, 2, 5), (0, 2, 5)],
        [(0, 2, 10), (1, 3, 1), (2, 4, 10)],
        [(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)],
    ]
    expected = [
        (0, []),
        (5, [(0, 3, 5)]),
        (7, [(0, 5, 3), (5, 10, 4)]),
        (8, [(0, 5, 4), (5, 10, 4)]),
        (10, [(0, 10, 10)]),
        (4, [(5, 6, 2), (8, 10, 2)]),
        (10, [(0, 2, 5), (2, 8, 5)]),
        (10, [(0, 10, 10)]),
        (10, [(0, 1, 5), (1, 2, 5)]),
        (20, [(0, 2, 10), (2, 4, 10)]),
        (2, [(0, 1, 1), (1, 2, 1)]),
    ]
    for iv, exp in zip(cases, expected):
        got = best_schedule(iv)
        assert got == exp, f"input={iv} got={got} exp={exp}"
    print("examples OK")


def test_random():
    rng = random.Random(12345)
    for t in range(3000):
        n = rng.randint(0, 9)
        maxc = rng.randint(1, 8)
        intervals = []
        for _ in range(n):
            a = rng.randint(0, maxc)
            b = rng.randint(a + 1, maxc + 2)
            p = rng.randint(1, 5)
            intervals.append((a, b, p))
        check(intervals)
    print("random OK")


def test_tiebreak_specific():
    # profit tie -> fewer intervals
    assert best_schedule([(0, 5, 5), (5, 10, 5), (0, 10, 10)]) == (10, [(0, 10, 10)])
    # profit tie -> more intervals wins when more profit
    assert best_schedule([(0, 1, 5), (1, 2, 5), (0, 2, 5)]) == (10, [(0, 1, 5), (1, 2, 5)])
    # touching intervals are allowed
    assert best_schedule([(0, 5, 1), (5, 10, 1)]) == (2, [(0, 5, 1), (5, 10, 1)])
    # identical intervals overlap -> at most one
    assert best_schedule([(3, 7, 4), (3, 7, 4)]) == (4, [(3, 7, 4)])
    print("tiebreak-specific OK")


if __name__ == "__main__":
    test_examples()
    test_tiebreak_specific()
    test_random()
    print("ALL TESTS PASSED")
