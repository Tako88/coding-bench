import sys
from solution import best_schedule

def run_tests():
    tests = [
        ([], (0, [])),
        ([(0, 3, 5)], (5, [(0, 3, 5)])),
        ([(0, 5, 3), (5, 10, 4)], (7, [(0, 5, 3), (5, 10, 4)])),
        ([(0, 5, 4), (5, 10, 4), (0, 10, 7)], (8, [(0, 5, 4), (5, 10, 4)])),
        ([(0, 10, 10), (1, 2, 1)], (10, [(0, 10, 10)])),
        ([(8, 10, 2), (5, 6, 2)], (4, [(5, 6, 2), (8, 10, 2)])),
        ([(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)], (10, [(0, 2, 5), (2, 8, 5)])),
        ([(0, 5, 5), (5, 10, 5), (0, 10, 10)], (10, [(0, 10, 10)])),
        ([(0, 1, 5), (1, 2, 5), (0, 2, 5)], (10, [(0, 1, 5), (1, 2, 5)])),
        ([(0, 2, 10), (1, 3, 1), (2, 4, 10)], (20, [(0, 2, 10), (2, 4, 10)])),
        ([(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)], (2, [(0, 1, 1), (1, 2, 1)])),
    ]
    for i, (intervals, expected) in enumerate(tests):
        result = best_schedule(intervals)
        if result != expected:
            print(f"Test {i} failed:")
            print("Input:", intervals)
            print("Expected:", expected)
            print("Got:", result)
            sys.exit(1)
    print("All tests passed!")

if __name__ == "__main__":
    run_tests()