"""Weighted interval scheduling with (profit, count, lexicographic) tie-breaks.

best_schedule(intervals)
    intervals: list of (start, end, profit) int tuples, 0 <= start < end, profit >= 1.
    Intervals occupy [start, end); two chosen intervals must not overlap
    (touching, end_a == start_b, is allowed).

    Returns (total_profit, chosen) where chosen is the chosen intervals as
    (start, end, profit) triples sorted ascending by (start, end, profit), among:
      1. max total profit,
      2. then min number of intervals,
      3. then lexicographically smallest sorted triple list.

    Runs in O(n log n).
"""

from bisect import bisect_left


def best_schedule(intervals):
    n = len(intervals)
    if n == 0:
        return (0, [])

    # Forward order: ascending (start, end, profit).
    ivs = sorted(intervals)
    starts = [iv[0] for iv in ivs]
    ends = [iv[1] for iv in ivs]
    profits = [iv[2] for iv in ivs]

    # f_prof[i] / f_cnt[i]: over all non-overlapping subsets of the forward
    # suffix starting at i, the maximum total profit, and the minimum number
    # of intervals among the subsets achieving that profit.  f[n] = (0, 0).
    #
    # If interval i is taken, the remaining intervals must all start at
    # >= ends[i]; in forward order those are exactly the suffix q(i)
    # starting at the first index j > i with starts[j] >= ends[i].
    f_prof = [0] * (n + 1)
    f_cnt = [0] * (n + 1)
    bl = bisect_left
    st = starts
    en = ends
    pr = profits
    for i in range(n - 1, -1, -1):
        q = bl(st, en[i], i + 1, n)
        take_p = pr[i] + f_prof[q]
        take_c = f_cnt[q] + 1
        skip_p = f_prof[i + 1]
        if take_p > skip_p:
            f_prof[i] = take_p
            f_cnt[i] = take_c
        elif take_p < skip_p:
            f_prof[i] = skip_p
            f_cnt[i] = f_cnt[i + 1]
        else:
            f_prof[i] = take_p
            sc = f_cnt[i + 1]
            f_cnt[i] = take_c if take_c < sc else sc

    total_profit = f_prof[0]
    min_count = f_cnt[0]

    # Greedy reconstruction in forward order.  Take interval i iff it is
    # compatible with everything already chosen and completing it to an
    # optimal (total_profit, min_count) set is possible; completing after i
    # is exactly the best (profit, count) of the suffix q(i).
    #
    # This yields the lexicographically smallest optimal set: at each step
    # the smallest (start, end, profit) triple that can appear next in some
    # optimal set is the one that appears in *the* lexicographically
    # smallest optimal set.
    chosen = []
    total = 0
    count = 0
    last_end = -1
    for i in range(n):
        s = st[i]
        if s < last_end:
            continue
        q = bl(st, en[i], i + 1, n)
        p = pr[i]
        if total + p + f_prof[q] == total_profit and count + 1 + f_cnt[q] == min_count:
            chosen.append((s, en[i], p))
            total += p
            count += 1
            last_end = en[i]

    return (total_profit, chosen)
