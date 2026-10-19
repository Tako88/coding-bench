"""Weighted interval scheduling with deterministic tie-breaks.

best_schedule(intervals) -> (total_profit, chosen)

Rules (from TASK.md):
  1. maximise total profit,
  2. then minimise the number of chosen intervals,
  3. then take the lexicographically smallest list of (start, end, profit) triples
     written in ascending triple order (element-by-element comparison).

Approach (O(n log n), fits 200k intervals easily):
  * Sort intervals ascending by (start, end, profit).  In any non-overlapping set the
    starts are strictly increasing and so are the ends, so sorting such a set by start
    == sorting by end == sorting by triple.  That makes the suffix DP exact and matches
    rule 3's ordering.
  * dp[i] = best (profit, min count) using only intervals with index >= i, computed
    right-to-left with dp[i] = better(dp[i+1], take i + dp[j[i]]), j[i] = first index
    whose start >= end[i].
  * Reconstruct greedily in triple order: pick the smallest feasible next interval,
    i.e. the first interval i (with start >= last chosen end) such that
    profit[i] + dp[j[i]] still delivers exactly the remaining profit AND
    1 + dp[j[i]].count is exactly the remaining count.  Both equalities are needed:
    they hold iff an optimal (max profit, min count) solution extends the prefix plus i.
"""

from bisect import bisect_left


def best_schedule(intervals):
    """Return (total_profit, chosen) per the spec in TASK.md."""
    ivs = sorted(tuple(t) for t in intervals)
    n = len(ivs)
    if n == 0:
        return (0, [])

    starts = [t[0] for t in ivs]
    ends = [t[1] for t in ivs]
    profits = [t[2] for t in ivs]

    # j[i] = first index whose start >= ends[i] (all indices >= j[i] can follow i)
    j_of = [0] * n
    for i in range(n):
        j_of[i] = bisect_left(starts, ends[i])

    # suffix DP over the sorted-by-start order
    best_profit = [0] * (n + 1)
    best_count = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        j = j_of[i]
        take_p = profits[i] + best_profit[j]
        take_c = best_count[j] + 1
        skip_p = best_profit[i + 1]
        skip_c = best_count[i + 1]
        if take_p > skip_p or (take_p == skip_p and take_c < skip_c):
            best_profit[i] = take_p
            best_count[i] = take_c
        else:
            best_profit[i] = skip_p
            best_count[i] = skip_c

    # greedy lexicographic reconstruction
    need_p = best_profit[0]
    need_c = best_count[0]
    chosen = []
    last_end = 0  # starts are >= 0 by spec, so everything is allowed initially
    i = 0
    while need_c > 0:
        while i < n:
            if starts[i] >= last_end:
                j = j_of[i]
                if (profits[i] + best_profit[j] == need_p
                        and best_count[j] + 1 == need_c):
                    chosen.append(ivs[i])
                    last_end = ends[i]
                    need_p -= profits[i]
                    need_c -= 1
                    i += 1
                    break
            i += 1
        else:
            break  # defensive; provably unreachable

    return (best_profit[0], chosen)
