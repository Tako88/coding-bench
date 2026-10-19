def best_schedule(intervals):
    if not intervals:
        return (0, [])

    # Sort by end time (primary), then start time (secondary) for deterministic ordering
    sorted_ints = sorted(intervals, key=lambda x: (x[1], x[0]))
    n = len(sorted_ints)

    # Precompute p[i]: the largest index j < i such that interval j ends <= interval i starts
    ends = [sorted_ints[i][1] for i in range(n)]
    starts = [sorted_ints[i][0] for i in range(n)]

    p = [-1] * n
    for i in range(n):
        lo, hi = 0, i - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if ends[mid] <= starts[i]:
                lo = mid + 1
            else:
                hi = mid - 1
        p[i] = hi

    # DP: for each prefix, store (profit, count, chosen_set)
    dp_profit = [0] * n
    dp_count = [0] * n
    dp_chosen = [None] * n

    for i in range(n):
        # Option 1: skip interval i
        if i == 0:
            skip_p, skip_c, skip_set = 0, 0, ()
        else:
            skip_p, skip_c, skip_set = dp_profit[i - 1], dp_count[i - 1], dp_chosen[i - 1]

        # Option 2: take interval i
        prev = p[i]
        if prev == -1:
            take_p = sorted_ints[i][2]
            take_c = 1
            take_set = (sorted_ints[i],)
        else:
            take_p = dp_profit[prev] + sorted_ints[i][2]
            take_c = dp_count[prev] + 1
            # Intervals in dp_chosen[prev] are non-overlapping and ordered by end time,
            # so appending at the end preserves sorted order.
            take_set = dp_chosen[prev] + (sorted_ints[i],)

        # Choose the better option according to the tie-breaking rules:
        # 1. Maximize profit
        # 2. Minimize count (fewer intervals)
        # 3. Lexicographic order of sorted intervals
        if skip_p > take_p:
            dp_profit[i] = skip_p
            dp_count[i] = skip_c
            dp_chosen[i] = skip_set
        elif skip_p < take_p:
            dp_profit[i] = take_p
            dp_count[i] = take_c
            dp_chosen[i] = take_set
        else:  # equal profit
            if skip_c < take_c:
                # skip has fewer intervals -> skip wins
                dp_profit[i] = skip_p
                dp_count[i] = skip_c
                dp_chosen[i] = skip_set
            elif skip_c > take_c:
                # take has fewer intervals -> take wins
                dp_profit[i] = take_p
                dp_count[i] = take_c
                dp_chosen[i] = take_set
            else:  # equal profit and count -> lexicographic tie-break
                if skip_set <= take_set:
                    dp_profit[i] = skip_p
                    dp_count[i] = skip_c
                    dp_chosen[i] = skip_set
                else:
                    dp_profit[i] = take_p
                    dp_count[i] = take_c
                    dp_chosen[i] = take_set

    # Final chosen set, sorted by (start, end, profit)
    chosen_sorted = tuple(
        sorted(dp_chosen[n - 1], key=lambda x: (x[0], x[1], x[2]))
    )
    return (dp_profit[n - 1], list(chosen_sorted))
