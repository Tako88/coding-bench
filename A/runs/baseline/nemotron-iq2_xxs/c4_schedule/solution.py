from bisect import bisect_right


def best_schedule(intervals):
    """Weighted interval scheduling with lexicographic tie-breaks.

    Returns (total_profit, chosen) where chosen is a list of (start, end, profit)
    triples ordered by ascending (start, end, profit).
    """
    if not intervals:
        return (0, [])

    # Sort by (end, start, profit).  For non-overlapping chosen intervals, end
    # order implies start order, so the DP build order is also the output order.
    iv = sorted(intervals, key=lambda x: (x[1], x[0], x[2]))
    n = len(iv)
    starts = [x[0] for x in iv]
    ends = [x[1] for x in iv]
    profits = [x[2] for x in iv]

    # p[i] = largest index j < i with ends[j] <= starts[i] (non-overlapping predecessor)
    p = [-1] * n
    for i in range(n):
        idx = bisect_right(ends, starts[i], 0, i)
        p[i] = idx - 1

    dp_profit = [0] * n
    dp_count = [0] * n
    dp_prev = [-1] * n
    dp_kind = [''] * n  # 'take' or 'skip'
    head = [None] * n   # first (smallest-start) triple of the solution, or None

    def get_seq(i):
        """Return the chosen triples for state i in output (ascending start) order."""
        res = []
        cur = i
        while cur != -1:
            if dp_kind[cur] == 'take':
                res.append(iv[cur])
                cur = dp_prev[cur]  # p[cur]
            else:
                cur = dp_prev[cur]  # cur - 1
        res.reverse()
        return res

    for i in range(n):
        # Skip candidate: best solution using intervals 0..i-1.
        if i == 0:
            skip_profit = 0
            skip_count = 0
            skip_head = None
        else:
            skip_profit = dp_profit[i - 1]
            skip_count = dp_count[i - 1]
            skip_head = head[i - 1]

        # Take candidate: best solution using intervals 0..p[i], plus interval i.
        pi = p[i]
        if pi >= 0:
            take_profit = profits[i] + dp_profit[pi]
            take_count = 1 + dp_count[pi]
            take_head = head[pi]
        else:
            take_profit = profits[i]
            take_count = 1
            take_head = iv[i]

        take_better = False
        if take_profit > skip_profit:
            take_better = True
        elif take_profit == skip_profit:
            if take_count < skip_count:
                take_better = True
            elif take_count == skip_count:
                # Rule 3: lexicographically smaller list of triples wins.
                if take_head is None:
                    take_better = True
                elif skip_head is None:
                    take_better = False
                elif take_head < skip_head:
                    take_better = True
                elif take_head > skip_head:
                    take_better = False
                else:
                    # Equal heads; compare the full sequences.
                    take_seq = (get_seq(pi) if pi >= 0 else []) + [iv[i]]
                    skip_seq = get_seq(i - 1)
                    if take_seq < skip_seq:
                        take_better = True
                    elif take_seq > skip_seq:
                        take_better = False
                    # else equal: keep the skip candidate.

        if take_better:
            dp_profit[i] = take_profit
            dp_count[i] = take_count
            dp_prev[i] = pi
            dp_kind[i] = 'take'
            head[i] = take_head
        else:
            dp_profit[i] = skip_profit
            dp_count[i] = skip_count
            dp_prev[i] = i - 1
            dp_kind[i] = 'skip'
            head[i] = skip_head

    chosen = get_seq(n - 1)
    return (dp_profit[n - 1], chosen)
