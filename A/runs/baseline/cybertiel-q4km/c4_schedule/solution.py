from bisect import bisect_left


def best_schedule(intervals):
    """Return (total_profit, chosen) for best weighted interval selection.

    Ordering of "best":
      1. maximize total profit,
      2. then minimize the number of chosen intervals,
      3. then minimize the sorted (start, end, profit) triple list lexicographically.
    """
    n = len(intervals)
    if n == 0:
        return (0, [])

    # Sort intervals by (start, end, profit).  For a feasible (pairwise
    # non-overlapping) set, starts are all distinct, so ascending start order
    # equals the rule-3 ordering.
    s = sorted(intervals, key=lambda x: (x[0], x[1], x[2]))
    starts = [iv[0] for iv in s]
    ends = [iv[1] for iv in s]
    profits = [iv[2] for iv in s]

    # Suffix DP.  dp[i] = best (profit, count) using only intervals with index
    # >= i (i.e. start >= starts[i]).  "best" = higher profit, then lower count.
    profit_dp = [0] * (n + 1)
    count_dp = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        e = ends[i]
        j = bisect_left(starts, e)  # first index with start >= e (touching allowed)
        inc_p = profits[i] + profit_dp[j]
        inc_c = 1 + count_dp[j]
        exc_p = profit_dp[i + 1]
        exc_c = count_dp[i + 1]
        if inc_p > exc_p or (inc_p == exc_p and inc_c < exc_c):
            profit_dp[i] = inc_p
            count_dp[i] = inc_c
        else:
            profit_dp[i] = exc_p
            count_dp[i] = exc_c

    total_profit = profit_dp[0]
    R_p = profit_dp[0]
    R_c = count_dp[0]

    chosen = []
    k = 0  # current suffix start (first index with start >= current boundary)
    while R_c > 0:
        i = k
        while True:
            e = ends[i]
            p = profits[i]
            j = bisect_left(starts, e)
            # i is a valid first choice iff taking it keeps us on an optimal
            # (profit, count) completion.
            if p + profit_dp[j] == R_p and 1 + count_dp[j] == R_c:
                break
            i += 1
        iv = s[i]
        chosen.append((iv[0], iv[1], iv[2]))
        R_p -= iv[2]
        R_c -= 1
        k = j  # next boundary's suffix start

    chosen.sort(key=lambda x: (x[0], x[1], x[2]))
    return (total_profit, chosen)
