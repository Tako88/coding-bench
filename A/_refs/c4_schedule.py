"""Reference solution for c4_schedule. Iterative DP over intervals sorted by
start, then one forward scan in (start, end, profit) order to build the
lexicographically smallest optimal list."""

import bisect


def best_schedule(intervals):
    n = len(intervals)
    if n == 0:
        return (0, [])
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], i))
    starts = [intervals[i][0] for i in order]
    profit_after = [0] * (n + 1)
    count_after = [0] * (n + 1)
    for k in range(n - 1, -1, -1):
        s, e, p = intervals[order[k]]
        j = bisect.bisect_left(starts, e, k + 1)
        take = (p + profit_after[j], 1 + count_after[j])
        skip = (profit_after[k + 1], count_after[k + 1])
        if take[0] > skip[0] or (take[0] == skip[0] and take[1] < skip[1]):
            profit_after[k], count_after[k] = take
        else:
            profit_after[k], count_after[k] = skip

    def after(e):
        j = bisect.bisect_left(starts, e)
        return (profit_after[j], count_after[j])

    scan = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1],
                                           intervals[i][2], i))
    chosen = []
    t = 0
    rem_p, rem_c = profit_after[0], count_after[0]
    for i in scan:
        if rem_p == 0:
            break
        s, e, p = intervals[i]
        if s < t:
            continue
        hp, hc = after(e)
        if p + hp == rem_p and 1 + hc == rem_c:
            chosen.append((s, e, p))
            t = e
            rem_p -= p
            rem_c -= 1
    return (profit_after[0], chosen)
