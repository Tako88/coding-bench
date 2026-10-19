def best_schedule(intervals):
    if not intervals:
        return (0, [])

    # Sort intervals by end time (tie-break: start asc, profit asc)
    sorted_intervals = sorted(intervals, key=lambda x: (x[1], x[0], x[2]))
    n = len(sorted_intervals)

    # Extract ends for binary search
    ends = [iv[1] for iv in sorted_intervals]

    # Binary search: find largest index j < i such that ends[j] <= start_i
    def find_prev(start_i, hi):
        lo, ans = 0, -1
        while lo <= hi:
            mid = (lo + hi) >> 1
            if ends[mid] <= start_i:
                ans = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return ans

    # DP: arrays for profit, count, and solution tuple
    dp_profit = [0] * n
    dp_count = [0] * n
    dp_solution = [()] * n

    for i in range(n):
        si, ei, pi = sorted_intervals[i]
        j = find_prev(si, i - 1)

        # Option A: include interval i
        if j >= 0:
            p_a = pi + dp_profit[j]
            c_a = 1 + dp_count[j]
            sol_a = merge_sorted(dp_solution[j], (si, ei, pi))
        else:
            p_a = pi
            c_a = 1
            sol_a = ((si, ei, pi),)

        # Option B: don't include interval i (take best from i-1)
        if i > 0:
            p_b = dp_profit[i - 1]
            c_b = dp_count[i - 1]
            sol_b = dp_solution[i - 1]
        else:
            p_b = 0
            c_b = 0
            sol_b = ()

        # Compare: profit desc, count asc, solution lex asc
        if p_a > p_b or (p_a == p_b and c_a < c_b) or \
           (p_a == p_b and c_a == c_b and sol_a < sol_b):
            dp_profit[i] = p_a
            dp_count[i] = c_a
            dp_solution[i] = sol_a
        else:
            dp_profit[i] = p_b
            dp_count[i] = c_b
            dp_solution[i] = sol_b

    return (dp_profit[n - 1], list(dp_solution[n - 1]))


def merge_sorted(sorted_tuple, new_element):
    """Insert new_element into sorted_tuple maintaining sort order.
    sorted_tuple is a tuple of (start, end, profit) triples sorted ascending."""
    lo, hi = 0, len(sorted_tuple)
    while lo < hi:
        mid = (lo + hi) >> 1
        if sorted_tuple[mid] < new_element:
            lo = mid + 1
        else:
            hi = mid
    return sorted_tuple[:lo] + (new_element,) + sorted_tuple[lo:]
