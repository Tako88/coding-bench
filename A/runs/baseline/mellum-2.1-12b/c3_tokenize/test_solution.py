import sys

sys.path.insert(0, '.')
from solution import tokenize

def run_tests():
    tests = [
        # Basic whitespace separated tokens
        ('a b c', ['a', 'b', 'c']),
        ('a    b', ['a', 'b']),
        ('', []),
        ('   \t ', []),
        ('--version', ['--version']),
        # Quoted strings
        ("'it'''s", ['its']),  # 'it''s'
        ('a\'\'b', ['ab']),  # a''b
        ('\'' \'', ['', '']),  # '' ''
        ('"" a', ['', 'a']),  # " a
        ('a"b" "c"d', ['ab', 'cd']),
        ('-x"y z"', ['-xy z']),
        ('a\ b', ['a b']),
        ('#a', ['#a']),
        ('a#b', ['a#b']),
        ('a #b', ['a']),
        ('#a', []),  # comment line
        ('"a\"b"', ['a"b']),
        ('"a\\b"', ['a\b']),
        ('"a\qb"', ['a\qb']),
        ("'a\b'", ['a\b']),
        ("'a#b'", ['a#b']),
        ('"a#b"', ['a#b']),
        # Error cases
        ('a\', None),  # backslash at end
        ("'abc", None),  # unclosed single quote
        ('"abc', None),  # unclosed double quote
    ]
    for i, (inp, expected) in enumerate(tests):
        try:
            result = tokenize(inp)
        except ValueError as e:
            if expected is None:
                print(f"Test {i+1} passed (expected error): {e}")
            else:
                print(f"Test {i+1} failed: expected {expected}, got exception {e}")
                return False
        except Exception as e:
            print(f"Test {i+1} failed: unexpected exception {e}")
            return False
        if result == expected:
            print(f"Test {i+1} passed: {inp} -> {result}")
        else:
            print(f"Test {i+1} failed: {inp} -> {result}, expected {expected}")
            return False
    return True

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)