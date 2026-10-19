import sys
sys.path.insert(0, '.')
from solution import shortest_prefix_match

def test():
    cases = [
        ('abc', 'abcdef', 3),
        ('a*c', 'abcde', 3),
        ('*', 'abc', 0),
        ('*', '', 0),
        ('a*', 'a', 1),
        ('*b', 'aaab', 4),
        ('**b', 'ab', 2),
        ('{ab,cd}', 'cdx', 2),
        ('{a,ab}c', 'abc', 3),
        ('{*,a}b', 'ab', 2),
        ('{,a}b', 'ab', 2),
        ('{}', 'ab', 0),
        ('a?c', 'abcd', 3),
        ('a\*b', 'a*bc', 3),
        ('a', '', -1),
        ('abc', 'ab', -1),
    ]
    all_passed = True
    for pattern, text, expected in cases:
        result = shortest_prefix_match(pattern, text)
        if result != expected:
            print(f"Failed: pattern={pattern!r}, text={text!r}, expected={expected}, got={result}")
            all_passed = False
    if all_passed:
        print("All tests passed!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    test()