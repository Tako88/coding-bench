import unittest
from solution import best_schedule


class TestBestSchedule(unittest.TestCase):
    """Test cases from the TASK.md examples plus edge cases."""

    # --- Examples from TASK.md ---

    def test_empty(self):
        self.assertEqual(best_schedule([]), (0, []))

    def test_single(self):
        self.assertEqual(best_schedule([(0, 3, 5)]), (5, [(0, 3, 5)]))

    def test_two_non_overlapping(self):
        self.assertEqual(
            best_schedule([(0, 5, 3), (5, 10, 4)]),
            (7, [(0, 5, 3), (5, 10, 4)])
        )

    def test_overlapping_choose_two_smaller(self):
        self.assertEqual(
            best_schedule([(0, 5, 4), (5, 10, 4), (0, 10, 7)]),
            (8, [(0, 5, 4), (5, 10, 4)])
        )

    def test_large_over_small(self):
        self.assertEqual(
            best_schedule([(0, 10, 10), (1, 2, 1)]),
            (10, [(0, 10, 10)])
        )

    def test_unsorted_input(self):
        self.assertEqual(
            best_schedule([(8, 10, 2), (5, 6, 2)]),
            (4, [(5, 6, 2), (8, 10, 2)])
        )

    def test_four_intervals(self):
        self.assertEqual(
            best_schedule([(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)]),
            (10, [(0, 2, 5), (2, 8, 5)])
        )

    # --- Tie-breaking examples ---

    def test_tie_profit_same_count_chooses_fewer_intervals(self):
        """Both small intervals give 10, but one interval is fewer."""
        self.assertEqual(
            best_schedule([(0, 5, 5), (5, 10, 5), (0, 10, 10)]),
            (10, [(0, 10, 10)])
        )

    def test_tie_profit_more_intervals_better(self):
        """Two intervals give 10 against 5 from the third."""
        self.assertEqual(
            best_schedule([(0, 1, 5), (1, 2, 5), (0, 2, 5)]),
            (10, [(0, 1, 5), (1, 2, 5)])
        )

    def test_two_high_profit_non_overlapping(self):
        self.assertEqual(
            best_schedule([(0, 2, 10), (1, 3, 1), (2, 4, 10)]),
            (20, [(0, 2, 10), (2, 4, 10)])
        )

    def test_duplicate_intervals(self):
        """Duplicate intervals: at most one of each identical pair."""
        self.assertEqual(
            best_schedule([(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)]),
            (2, [(0, 1, 1), (1, 2, 1)])
        )

    # --- Additional edge cases ---

    def test_all_overlapping_same_profit(self):
        """All overlap, same profit: pick one."""
        self.assertEqual(
            best_schedule([(0, 5, 5), (1, 6, 5), (2, 7, 5)]),
            (5, [(0, 5, 5)])
        )

    def test_all_overlapping_different_profit(self):
        """All overlap, different profits: pick the best."""
        self.assertEqual(
            best_schedule([(0, 10, 3), (1, 9, 7), (2, 8, 5)]),
            (7, [(1, 9, 7)])
        )

    def test_chained_non_overlapping(self):
        """Many non-overlapping intervals in a chain."""
        intervals = [(i, i + 1, 1) for i in range(10)]
        result = best_schedule(intervals)
        self.assertEqual(result[0], 10)
        self.assertEqual(len(result[1]), 10)

    def test_touching_intervals(self):
        """Intervals that touch (end_a == start_b) should both be chosen."""
        self.assertEqual(
            best_schedule([(0, 1, 5), (1, 2, 5), (2, 3, 5)]),
            (15, [(0, 1, 5), (1, 2, 5), (2, 3, 5)])
        )

    def test_lex_tiebreak_same_profit_same_count(self):
        """Same profit and count, choose lexicographically smaller solution."""
        # Both solutions give profit 10 with 2 intervals
        # Option 1: (0,3,5) + (3,6,5) -> sorted: [(0,3,5), (3,6,5)]
        # Option 2: (1,4,5) + (4,7,5) -> sorted: [(1,4,5), (4,7,5)]
        # Option 1 is lex smaller because (0,3,5) < (1,4,5)
        self.assertEqual(
            best_schedule([(0, 3, 5), (3, 6, 5), (1, 4, 5), (4, 7, 5)]),
            (10, [(0, 3, 5), (3, 6, 5)])
        )

    def test_single_interval_zero_profit_not_allowed(self):
        """Profit >= 1 always, so single interval always chosen."""
        self.assertEqual(
            best_schedule([(0, 1, 1)]),
            (1, [(0, 1, 1)])
        )

    def test_large_profit_over_small(self):
        """Big profit interval beats many small ones."""
        self.assertEqual(
            best_schedule([(0, 100, 1000), (0, 1, 1), (1, 2, 1), (2, 3, 1)]),
            (1000, [(0, 100, 1000)])
        )

    def test_multiple_overlapping_same_profit_lex(self):
        """Multiple overlapping intervals with same profit, lex tiebreak."""
        # (0,5,5) and (5,10,5) give 10 with 2 intervals
        # (0,10,10) gives 10 with 1 interval -> fewer intervals wins
        self.assertEqual(
            best_schedule([(0, 5, 5), (5, 10, 5), (0, 10, 10)]),
            (10, [(0, 10, 10)])
        )

    def test_identical_intervals(self):
        """Identical intervals: can only pick one."""
        self.assertEqual(
            best_schedule([(0, 5, 5), (0, 5, 5), (0, 5, 5)]),
            (5, [(0, 5, 5)])
        )

    def test_many_small_one_big(self):
        """One big interval vs many small ones that sum up more."""
        self.assertEqual(
            best_schedule(
                [(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 4, 1), (4, 5, 1),
                 (0, 5, 3)]
            ),
            (5, [(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 4, 1), (4, 5, 1)])
        )

    def test_result_sorted_by_start(self):
        """Result intervals should be sorted by (start, end, profit)."""
        result = best_schedule([(5, 10, 4), (0, 5, 3)])
        self.assertEqual(result[0], 7)
        self.assertEqual(result[1], [(0, 5, 3), (5, 10, 4)])

    def test_complex_lex_tiebreak(self):
        """Complex case where lex tiebreak matters."""
        # Two ways to get profit 8:
        # A: (0,5,4) + (5,10,4) -> sorted [(0,5,4), (5,10,4)]
        # B: (0,10,7) -> sorted [(0,10,7)] -> only 1 interval, fewer wins
        self.assertEqual(
            best_schedule([(0, 5, 4), (5, 10, 4), (0, 10, 7)]),
            (8, [(0, 5, 4), (5, 10, 4)])
        )


if __name__ == '__main__':
    unittest.main()
