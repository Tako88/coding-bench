from solution import best_schedule

cases = [
    ([], (0, [])),
    ([(0, 3, 5)], (5, [(0, 3, 5)])),
    ([(0, 5, 3), (5, 10, 4)], (7, [(0, 5, 3), (5, 10, 4)])),
    ([(0, 5, 4), (5, 10, 4), (0, 10, 7)], (8, [(0, 5, 4), (5, 10, 4)])),
    ([(0, 10, 10), (1, 2, 1)], (10, [(0, 10, 10)])),
    ([(8, 10, 2), (5, 6, 2)], (4, [(5, 6, 2), (8, 10, 2)])),
    ([(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)],
     (10, [(0, 2, 5), (2, 8, 5)])),
    ([(0, 5, 5), (5, 10, 5), (0, 10, 10)],
     (10, [(0, 10, 10)])),
    ([(0, 1, 5), (1, 2, 5), (0, 2, 5)],
     (10, [(0, 1, 5), (1, 2, 5)])),
    ([(0, 2, 10), (1, 3, 1), (2, 4, 10)],
     (20, [(0, 2, 10), (2, 4, 10)])),
    ([(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)],
     (2, [(0, 1, 1), (1, 2, 1)])),
]

def check(name, intervals, expected):
    got = best_schedule(list(intervals))
    ok = got == expected
    print(f"{'OK ' if ok else 'FAIL'} {name}: got={got} expected={expected}")
    return ok

all_ok = True
for idx, (intervals, expected) in enumerate(cases):
    all_ok &= check(f"ex{idx}", intervals, expected)

# Edge: identical intervals (overlap each other, at most one chosen)
all_ok &= check("identical", [(0, 2, 5), (0, 2, 5)], (5, [(0, 2, 5)]))

# Edge: touching intervals allowed
all_ok &= check("touching", [(0, 2, 3), (2, 4, 3)], (6, [(0, 2, 3), (2, 4, 3)]))

# Edge: all profit 1 -> max profit = max count; min count = max profit;
# lex smallest max-count set.
all_ok &= check("unit_profit", [(0, 3, 1), (1, 2, 1), (2, 4, 1), (3, 5, 1)],
                (2, [(0, 3, 1), (3, 5, 1)]))

# Large random performance test: distinct profits -> decisions by profit, O(n log n)
import random
random.seed(12345)
n = 200000
intervals = []
for _ in range(n):
    s = random.randint(0, 10**9)
    e = s + random.randint(1, 1000)
    profit = random.randint(1, 10**9)
    intervals.append((s, e, profit))
import time
t0 = time.time()
profit, chosen = best_schedule(intervals)
t1 = time.time()
print(f"large n={n}: profit={profit} chosen_len={len(chosen)} time={t1-t0:.2f}s")
# verify chosen is non-overlapping and sorted
ok = True
prev_end = -1
for tri in chosen:
    s, e, pr = tri
    if s < prev_end:
        ok = False
        print("  OVERLAP in chosen!")
    prev_end = e
# sorted by (start,end,profit)?
sorted_ok = chosen == sorted(chosen, key=lambda x: (x[0], x[1], x[2]))
print(f"  non_overlap={ok} sorted={sorted_ok}")
all_ok &= ok and sorted_ok and (t1 - t0) < 3.0

# Tie-heavy performance test: all profit 1, moderate size
random.seed(999)
n = 50000
intervals = [(random.randint(0, 10**6), random.randint(1, 10**6) + random.randint(0, 10**6), 1)
             for _ in range(n)]
# ensure end > start
intervals = [(s, e, 1) for s, e, _ in intervals if e > s] or intervals
intervals = [(s, max(e, s + 1), 1) for s, e, _ in intervals]
t0 = time.time()
profit, chosen = best_schedule(intervals)
t1 = time.time()
print(f"tieheavy n={len(intervals)}: profit={profit} chosen_len={len(chosen)} time={t1-t0:.2f}s")
prev_end = -1
ok = True
for tri in chosen:
    s, e, pr = tri
    if s < prev_end:
        ok = False
    prev_end = e
sorted_ok = chosen == sorted(chosen, key=lambda x: (x[0], x[1], x[2]))
print(f"  non_overlap={ok} sorted={sorted_ok}")
all_ok &= ok and sorted_ok

print("ALL OK" if all_ok else "SOME FAILED")
