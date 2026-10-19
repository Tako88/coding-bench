from solution import best_schedule

def test_empty():
    result = best_schedule([])
    assert result == (0, []), f"Empty: {result}"
    print("PASS: empty input ->", result)

def test_single():
    result = best_schedule([(0, 3, 5)])
    assert result == (5, [(0, 3, 5)]), f"Single: {result}"
    print("PASS: single interval ->", result)

def test_two_non_overlapping():
    result = best_schedule([(0, 5, 3), (5, 10, 4)])
    assert result == (7, [(0, 5, 3), (5, 10, 4)]), f"Two non-overlapping: {result}"
    print("PASS: two non-overlapping ->", result)

def test_three_with_overlap():
    result = best_schedule([(0, 5, 4), (5, 10, 4), (0, 10, 7)])
    assert result == (8, [(0, 5, 4), (5, 10, 4)]), f"Three with overlap: {result}"
    print("PASS: three intervals ->", result)

def test_two_small_vs_one_large():
    result = best_schedule([(0, 10, 10), (1, 2, 1)])
    assert result == (10, [(0, 10, 10)]), f"Large vs small: {result}"
    print("PASS: large vs small ->", result)

def test_touching_intervals():
    result = best_schedule([(8, 10, 2), (5, 6, 2)])
    assert result == (4, [(5, 6, 2), (8, 10, 2)]), f"Touching: {result}"
    print("PASS: touching intervals ->", result)

def test_four_intervals():
    result = best_schedule([(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)])
    assert result == (10, [(0, 2, 5), (2, 8, 5)]), f"Four intervals: {result}"
    print("PASS: four intervals ->", result)

def test_both_small_vs_one_large():
    result = best_schedule([(0, 5, 5), (5, 10, 5), (0, 10, 10)])
    assert result == (10, [(0, 10, 10)]), f"Both small: {result}"
    print("PASS: both small vs one large ->", result)

def test_two_small_vs_one_large_twice():
    result = best_schedule([(0, 1, 5), (1, 2, 5), (0, 2, 5)])
    assert result == (10, [(0, 1, 5), (1, 2, 5)]), f"Two small vs one: {result}"
    print("PASS: two small vs one ->", result)

def test_interval_repetition():
    result = best_schedule([(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)])
    assert result == (2, [(0, 1, 1), (1, 2, 1)]), f"Repetition: {result}"
    print("PASS: interval repetition ->", result)

def test_weighted_interval_scheduling():
    result = best_schedule([(0, 2, 10), (1, 3, 1), (2, 4, 10)])
    assert result == (20, [(0, 2, 10), (2, 4, 10)]), f"Weighted: {result}"
    print("PASS: weighted interval ->", result)

def test_lexicographic_order():
    # Two optimal solutions with same profit and count; pick lexicographically smallest
    result = best_schedule([(0, 5, 5), (5, 10, 5), (0, 10, 10)])
    assert result == (10, [(0, 10, 10)]), f"Lexicographic: {result}"
    print("PASS: lexicographic order ->", result)

if __name__ == "__main__":
    test_empty()
    test_single()
    test_two_non_overlapping()
    test_three_with_overlap()
    test_two_small_vs_one_large()
    test_touching_intervals()
    test_four_intervals()
    test_both_small_vs_one_large()
    test_two_small_vs_one_large_twice()
    test_interval_repetition()
    test_weighted_interval_scheduling()
    test_lexicographic_order()
    print("\nAll tests passed!")
