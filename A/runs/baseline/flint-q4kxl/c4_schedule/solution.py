from bisect import bisect_left


def best_schedule(intervals):
    n = len(intervals)
    if n == 0:
        return (0, [])

    ivs = sorted(intervals, key=lambda t: (t[0], t[1], t[2]))
    starts = [t[0] for t in ivs]
    ends = [t[1] for t in ivs]
    profits = [t[2] for t in ivs]

    # nxt[k] = first index i such that starts[i] >= ends[k]
    # (intervals with start >= end of interval k are compatible with k)
    nxt = [bisect_left(starts, ends[k]) for k in range(n)]

    # Suffix DP: bestP[k] = max profit using only intervals[k:], bestC[k] =
    # min number of intervals achieving bestP[k].
    bestP = [0] * (n + 1)
    bestC = [0] * (n + 1)
    for k in range(n - 1, -1, -1):
        j = nxt[k]
        tp = profits[k] + bestP[j]
        cp = 1 + bestC[j]
        if tp > bestP[k + 1] or (tp == bestP[k + 1] and cp < bestC[k + 1]):
            bestP[k] = tp
            bestC[k] = cp
        else:
            bestP[k] = bestP[k + 1]
            bestC[k] = bestC[k + 1]

    total_profit = bestP[0]
    count = bestC[0]

    chosen = []
    remaining_profit = total_profit
    remaining_count = count
    k = 0  # start of current residual suffix

    while remaining_count > 0:
        found = -1
        idx = k
        while idx < n:
            s, e, p = ivs[idx]
            j = nxt[idx]
            if bestP[j] == remaining_profit - p and bestC[j] == remaining_count - 1:
                found = idx
                break
            idx += 1
        # A feasible interval must exist here (invariant of the greedy).
        s, e, p = ivs[found]
        chosen.append((s, e, p))
        remaining_profit -= p
        remaining_count -= 1
        k = nxt[found]

    return (total_profit, chosen)
