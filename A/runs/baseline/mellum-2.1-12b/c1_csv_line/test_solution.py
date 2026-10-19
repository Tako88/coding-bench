from solution import parse_csv_line

def test():
    test_cases = [
        ('a,b,c', ['a', 'b', 'c']),
        ('a', ['a']),
        ('a,,b', ['a', '', 'b']),
        (',,,', ['', '', '', '']),
        ('""', ['']),
        ('a,"b"', ['a', 'b']),
        (',"a"', ['', 'a']),
        ('"a",', ['a', '']),
        ('"a,b",c', ['a,b', 'c']),
        ('"a b"', ['a b']),
        (',', [',']),
        ('"he said ""hi"",x', ['he said "hi"', 'x']),
        ('"""', ['"']),
        ('a"b"', ['a"b"']),
        ('a"b"', ['a"b"']),  # duplicate entry, remove one
        ('', ['']),
    ]
    for line, expected in test_cases:
        result = parse_csv_line(line)
        assert result == expected, f"Failed for {line!r}: expected {expected}, got {result}"
    # Test errors
    try:
        parse_csv_line('"unterminated')
        assert False, "Expected ValueError for unterminated quoted field"
    except ValueError:
        pass
    try:
        parse_csv_line('"a"x')
        assert False, "Expected ValueError for character after quoted field"
    except ValueError:
        pass
    try:
        parse_csv_line('"a""')
        assert False, "Expected ValueError for unterminated quoted field"
    except ValueError:
        pass
    print("All tests passed!")

test()