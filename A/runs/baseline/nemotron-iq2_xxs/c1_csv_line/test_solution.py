import solution


def test_examples():
    cases = [
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
        ('"' + ',' + '"', [',']),
        ('"he said ""hi""",x', ['he said "hi"', 'x']),
        ('""""', ['"']),
        ('a"b', ['a"b']),
        ('a"b"', ['a"b"']),
        ('', ['']),
    ]
    for line, expected in cases:
        assert solution.parse_csv_line(line) == expected, (repr(line), expected)


def test_errors():
    for line in ['"unterminated', '"a"x', '"a""']:
        try:
            solution.parse_csv_line(line)
        except ValueError:
            continue
        raise AssertionError('expected ValueError for %r' % line)


def test_edge_cases():
    # Empty fields around commas.
    assert solution.parse_csv_line('a,') == ['a', '']
    assert solution.parse_csv_line(',a') == ['', 'a']
    assert solution.parse_csv_line(',') == ['', '']

    # Quoted empty field in the middle.
    assert solution.parse_csv_line('a,"",b') == ['a', '', 'b']

    # Quoted field followed by more unquoted content.
    assert solution.parse_csv_line('"a",b') == ['a', 'b']

    # Six quotes: open, escaped-quote, escaped-quote, close => two literal quotes.
    assert solution.parse_csv_line('""""""') == [chr(34) * 2]

    # Quoted field containing an escaped quote then more text.
    assert solution.parse_csv_line('"a""b"') == ['a"b']

    # A double quote inside an unquoted field is just a literal.
    assert solution.parse_csv_line('a"b"c') == ['a"b"c']

    # Single character fields.
    assert solution.parse_csv_line('"x"') == ['x']

    # Quoted field with a comma and spaces.
    assert solution.parse_csv_line('"a, b"') == ['a, b']


def main():
    test_examples()
    test_errors()
    test_edge_cases()
    print('all tests passed')


if __name__ == '__main__':
    main()
