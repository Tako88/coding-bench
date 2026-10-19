from bisect import bisect_left
from collections import defaultdict


def best_schedule(intervals):
    """
    Choose a non-overlapping subset of intervals maximizing, in order:
      1. total profit (max)
      2. fewest intervals (min count)
      3. lexicographically smallest list of (start, end, profit) triples
         when the chosen triples are sorted ascending by (start, end, profit).

    Returns (total_profit, chosen) where chosen is ordered ascending by
    (start, end, profit).
    """
    n = len(intervals)
    if n == 0:
        return (0, [])

    # Sort intervals by (start, end, profit). `s` holds the triples in that order.
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], intervals[i][2]))
    s = [intervals[i] for i in order]
    starts = [t[0] for t in s]
    ends = [t[1] for t in s]
    profits = [t[2] for t in s]

    # Suffix DP: g[j] = (max_profit, min_count) achievable using a subset of
    # intervals[j..] (all have start >= starts[j]).  g[n] = (0, 0).
    # Taking interval j requires the next interval to start >= end_j.
    gp = [0] * (n + 1)
    gc = [0] * (n + 1)
    for j in range(n - 1, -1, -1):
        k = bisect_left(starts, ends[j])  # first index with start >= end_j
        tp = profits[j] + gp[k]           # take interval j
        tc = 1 + gc[k]
        sp = gp[j + 1]                    # skip interval j
        sc = gc[j + 1]
        if tp > sp or (tp == sp and tc < sc):
            gp[j] = tp
            gc[j] = tc
        else:
            gp[j] = sp
            gc[j] = sc

    P = gp[0]
    C = gc[0]
    if C == 0:
        return (0, [])

    # reach(end_i) = best suffix profit/count for intervals starting at/after end_i.
    # For interval i, signature (A, B) = (profit_i + Rp, 1 + Rc) where
    # (Rp, Rc) = reach(end_i).  An interval i can be the next chosen interval
    # from a state with remaining (rem_p, rem_c) iff its signature equals
    # (rem_p, rem_c) and its start >= current deadline.
    buckets = defaultdict(list)
    for j in range(n):
        rj = bisect_left(starts, ends[j])
        Rp = gp[rj]
        Rc = gc[rj]
        A = profits[j] + Rp
        B = 1 + Rc
        buckets[(A, B)].append((starts[j], ends[j], profits[j], j))

    bucket_data = {}
    bucket_starts = {}
    for sig, lst in buckets.items():
        lst.sort()  # ascending by (start, end, profit, index)
        bucket_data[sig] = lst
        bucket_starts[sig] = [t[0] for t in lst]

    # Greedy reconstruction of the lexicographically smallest optimal solution.
    result = []
    cur_j = 0
    while gc[cur_j] > 0:
        Pj = gp[cur_j]
        Cj = gc[cur_j]
        d = starts[cur_j]  # next interval must have start >= d
        sig = (Pj, Cj)
        lst = bucket_data[sig]
        starts_arr = bucket_starts[sig]
        pos = bisect_left(starts_arr, d)
        st, en, pr, orig = lst[pos]
        result.append(s[orig])
        cur_j = bisect_left(starts, en)

    return (P, result)
