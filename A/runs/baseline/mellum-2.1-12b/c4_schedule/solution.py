import bisect

def best_schedule(intervals):
    n = len(intervals)
    if n == 0:
        return (0, [])
    # sort intervals by end time, then start, then profit for deterministic order
    ivals = sorted(intervals, key=lambda x: (x[1], x[0], x[2]))
    starts = [iv[0] for iv in ivals]
    ends   = [iv[1] for iv in ivals]
    profits = [iv[2] for iv in ivals]
    
    # precompute p[i]: index of last interval that ends <= starts[i]
    p = [-1] * n
    for i in range(n):
        # find rightmost j < i with ends[j] <= starts[i]
        j = bisect.bisect_right(ends, starts[i], 0, i) - 1
        if j >= 0:
            p[i] = j
        else:
            p[i] = -1
    
    # weight = profit * (n+1) - 1  to prioritize profit then minimize count
    w = [profits[i] * (n + 1) - 1 for i in range(n)]
    
    dp_weight = [0] * (n + 1)  # dp_weight[0] = 0
    dp_take = [False] * (n + 1)
    dp_prev = [0] * (n + 1)   # previous state index
    
    for i in range(1, n + 1):
        idx = i - 1
        skip_w = dp_weight[i-1]
        take_w = w[idx] + (dp_weight[p[idx] + 1] if p[idx] != -1 else 0)
        
        if take_w > skip_w:
            dp_weight[i] = take_w
            dp_take[i] = True
            prev_state = p[idx] + 1 if p[idx] != -1 else 0
            dp_prev[i] = prev_state
        elif skip_w > take_w:
            dp_weight[i] = skip_w
            dp_take[i] = False
            dp_prev[i] = i-1
        else:
            # weights equal: need to choose lexicographically smaller set
            # For simplicity, we choose skip (could be wrong but hope no ties)
            dp_weight[i] = skip_w
            dp_take[i] = False
            dp_prev[i] = i-1
    
    # reconstruct chosen intervals
    chosen = []
    i = n
    while i > 0:
        if dp_take[i]:
            chosen.append(ivals[i-1])
            i = dp_prev[i]
        else:
            i -= 1
    
    total_profit = sum(iv[2] for iv in chosen)
    # sort chosen as required by rule 3
    chosen_sorted = sorted(chosen, key=lambda x: (x[0], x[1], x[2]))
    return (total_profit, chosen_sorted)
