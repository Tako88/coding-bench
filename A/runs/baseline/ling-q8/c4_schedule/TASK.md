# weighted scheduling with tie-breaks

Implement best_schedule(intervals) in solution.py.

intervals is a list of (start, end, profit) tuples of ints with 0 <= start < end and
profit >= 1. An interval occupies the half-open range [start, end): it covers start and
does not cover end. Two intervals may both be chosen only if they do not overlap, which
means end_a <= start_b or end_b <= start_a for the two chosen intervals a and b. Two
intervals that merely touch, with end_a == start_b, do NOT overlap and may both be chosen.

Choose a subset of the given intervals such that:

  1. its total profit is as large as possible, then
  2. among all subsets with that total profit, its number of intervals is as small as
     possible, then
  3. among all subsets satisfying 1 and 2, it is smallest in this order: write the chosen
     intervals as (start, end, profit) triples in ascending order of (start, end, profit),
     and compare two such lists element by element, starting from the first element. The
     first element where they differ decides, and the smaller triple is the smaller list.

Return the pair (total_profit, chosen) where total_profit is the total profit of the
chosen subset as an int, and chosen is the list of the chosen intervals as (start, end,
profit) triples, ordered as described in rule 3. The empty subset is allowed and has
total profit 0 and an empty list. An empty input gives (0, []).

Intervals with identical values are allowed and are separate intervals: two identical
intervals overlap each other, so at most one of them can be chosen.

PERFORMANCE: intervals may contain up to 200,000 entries and the call must finish within
3 seconds. A dynamic program over all pairs of intervals will not pass.

EXAMPLES

  []                                     -> (0, [])
  [(0, 3, 5)]                            -> (5, [(0, 3, 5)])
  [(0, 5, 3), (5, 10, 4)]                -> (7, [(0, 5, 3), (5, 10, 4)])
  [(0, 5, 4), (5, 10, 4), (0, 10, 7)]    -> (8, [(0, 5, 4), (5, 10, 4)])
  [(0, 10, 10), (1, 2, 1)]               -> (10, [(0, 10, 10)])
  [(8, 10, 2), (5, 6, 2)]                -> (4, [(5, 6, 2), (8, 10, 2)])
  [(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)] -> (10, [(0, 2, 5), (2, 8, 5)])

  [(0, 5, 5), (5, 10, 5), (0, 10, 10)]   -> (10, [(0, 10, 10)])
      both small intervals give 10, but one interval is fewer

  [(0, 1, 5), (1, 2, 5), (0, 2, 5)]      -> (10, [(0, 1, 5), (1, 2, 5)])
      two intervals give 10 against 5 from the third

  [(0, 2, 10), (1, 3, 1), (2, 4, 10)]    -> (20, [(0, 2, 10), (2, 4, 10)])

  [(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)] -> (2, [(0, 1, 1), (1, 2, 1)])
