import random
from itertools import combinations

from solution import best_schedule


def brute2(intervals):
    n = len(intervals)
    best = None  # tuple (profit, -count, triples) with correct ordering semantics
    def better(cand, cur):
        if cur is None:
            return True
        cp, cc, ct = cur
        kp, kc, kt = cand
        if kp != cp:
            return kp > cp
        if kc != cc:
            return kc > cc  # -count: larger means fewer intervals
        return kt < ct
    for r in range(n + 1):
        for combo in combinations(range(n), r):
            chosen = [intervals[i] for i in combo]
            se = sorted((s, e) for (s, e, p) in chosen)
            ok = True
            for idx in range(1, len(se)):
                if se[idx - 1][1] > se[idx][0]:
                    ok = False
                    break
            if not ok:
                continue
            profit = sum(p for (s, e, p) in chosen)
            count = len(chosen)
            triples = sorted(chosen)
            cand = (profit, -count, triples)
            if better(cand, best):
                best = cand
    if best is None:
        return (0, [])
    return (best[0], best[2])


def run_case(name, intervals, expected=None):
    got = best_schedule(intervals)
    if expected is not None:
        assert got == expected, f"{name}: got {got}, expected {expected}"
    # cross-check against brute force
    bf = brute2(intervals)
    assert got == bf, f"{name}: got {got}, brute {bf}, intervals {intervals}"
    print(f"OK {name}: {got}")


def main():
    run_case("empty", [], (0, []))
    run_case("single", [(0, 3, 5)], (5, [(0, 3, 5)]))
    run_case("touch", [(0, 5, 3), (5, 10, 4)], (7, [(0, 5, 3), (5, 10, 4)]))
    run_case("split_vs_one", [(0, 5, 4), (5, 10, 4), (0, 10, 7)],
             (8, [(0, 5, 4), (5, 10, 4)]))
    run_case("big_plus_tiny", [(0, 10, 10), (1, 2, 1)], (10, [(0, 10, 10)]))
    run_case("reorder", [(8, 10, 2), (5, 6, 2)], (4, [(5, 6, 2), (8, 10, 2)]))
    run_case("chain", [(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)],
             (10, [(0, 2, 5), (2, 8, 5)]))
    run_case("two_fewer", [(0, 5, 5), (5, 10, 5), (0, 10, 10)],
             (10, [(0, 10, 10)]))
    run_case("two_vs_one", [(0, 1, 5), (1, 2, 5), (0, 2, 5)],
             (10, [(0, 1, 5), (1, 2, 5)]))
    run_case("gap", [(0, 2, 10), (1, 3, 1), (2, 4, 10)],
             (20, [(0, 2, 10), (2, 4, 10)]))
    run_case("idents", [(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)],
             (2, [(0, 1, 1), (1, 2, 1)]))

    # Extra edge cases
    # identical intervals overlap: at most one
    run_case("identical", [(0, 5, 7), (0, 5, 7)], (7, [(0, 5, 7)]))
    # rule 3: same profit & count, prefer smaller triples
    run_case("lex_rule3", [(0, 4, 5), (4, 8, 5), (0, 2, 5), (2, 8, 5)],
             None)
    # all overlapping -> pick single best
    run_case("all_overlap", [(0, 10, 3), (1, 9, 8), (2, 8, 5)],
             (8, [(1, 9, 8)]))

    # Randomized cross-checks against brute force
    rng = random.Random(12345)
    for it in range(3000):
        n = rng.randint(0, 8)
        ivs = []
        for _ in range(n):
            a = rng.randint(0, 8)
            b = rng.randint(a + 1, a + 4)
            p = rng.randint(1, 6)
            ivs.append((a, b, p))
        run_case(f"rand{it}", ivs)

    # Larger random for the lex tie-break stress (still brute- feasible)
    for it in range(300):
        n = rng.randint(0, 10)
        ivs = []
        for _ in range(n):
            a = rng.randint(0, 6)
            b = rng.randint(a + 1, a + 3)
            p = rng.randint(1, 3)
            ivs.append((a, b, p))
        run_case(f"randbig{it}", ivs)

    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
