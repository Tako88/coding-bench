"""Weighted interval scheduling with tie-breaks.

Chooses a non-overlapping subset of intervals maximizing, in order:
  1. total profit
  2. then minimizing the number of intervals
  3. then the lexicographically smallest list of (start, end, profit)
     triples, written in ascending order of (start, end, profit).

Algorithm (O(n log n)):
  * Sort intervals by (start, end, profit).  In this order, a non-overlapping
    subset is exactly a sequence of increasing indices where each next pick
    has index >= nxt[i] (the first index with start >= end_i), and the pick
    order equals the required output order (index order == triple order).
  * Backward DP: prof[i] = max profit from indices >= i;
    cnt[i] = min number of intervals among subsets achieving prof[i].
  * Greedy reconstruction: at state (i, R, C) [invariant: prof[i] == R and
    cnt[i] == C], the next pick is the smallest index j >= i that can be
    extended to a full (total, cnt[0]) solution, i.e.
        w[j] + prof[nxt[j]] == R  and  cnt[nxt[j]] + 1 == C.
    Scanning from i upward, ranges visited across all steps are disjoint
    (after picking j we jump to nxt[j] > j), so reconstruction is O(n).
"""

from bisect import bisect_left


def best_schedule(intervals):
    n = len(intervals)
    if n == 0:
        return (0, [])

    iv = sorted(tuple(t) for t in intervals)
    s = [0] * n
    e = [0] * n
    w = [0] * n
    for i, (a, b, c) in enumerate(iv):
        s[i] = a
        e[i] = b
        w[i] = c

    # nxt[i] = first index j with start_j >= end_i (touching is allowed)
    nxt = [bisect_left(s, e[i]) for i in range(n)]

    # prof[i] = max total profit using a subset of indices >= i
    # cnt[i]  = min number of intervals among subsets achieving prof[i]
    prof = [0] * (n + 1)
    cnt = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        take_p = w[i] + prof[nxt[i]]
        skip_p = prof[i + 1]
        if take_p > skip_p:
            prof[i] = take_p
            cnt[i] = cnt[nxt[i]] + 1
        elif take_p < skip_p:
            prof[i] = skip_p
            cnt[i] = cnt[i + 1]
        else:
            prof[i] = take_p
            take_c = cnt[nxt[i]] + 1
            skip_c = cnt[i + 1]
            cnt[i] = take_c if take_c < skip_c else skip_c

    total = prof[0]

    # Greedy reconstruction (invariant: prof[i] == R, cnt[i] == C)
    chosen = []
    i = 0
    R = total
    C = cnt[0]
    while C:
        while w[i] + prof[nxt[i]] != R or cnt[nxt[i]] + 1 != C:
            i += 1
            assert i < n, "no feasible pick found"
        chosen.append((s[i], e[i], w[i]))
        R -= w[i]
        i = nxt[i]
        C -= 1

    return (total, chosen)
