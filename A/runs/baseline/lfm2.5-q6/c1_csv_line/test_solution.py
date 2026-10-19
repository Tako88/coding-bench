import pytest
from solution import parse_csv_line


def test_empty_line():
    assert parse_csv_line('') == ['']


def test_simple_fields():
    assert parse_csv_line('a,b,c') == ['a', 'b', 'c']
    assert parse_csv_line('a') == ['a']
    assert parse_csv_line('a,,b') == ['a', '', 'b']
    assert parse_csv_line(',,,') == ['', '', '', '']


def test_quoted_fields():
    # Quoted fields with content
    assert parse_csv_line('"a,b"') == ['a,b']
    assert parse_csv_line('"a b"') == ['a b']
    assert parse_csv_line('"he said ""hi"",x') == ['he said "hi"', 'x']
    assert parse_csv_line('""""') == ['"']
    # Quoted empty field
    assert parse_csv_line('""') == ['']
    # Quoted field with trailing comma
    assert parse_csv_line('"a",') == ['a', '']
    # Quoted field containing a quote
    assert parse_csv_line('a"b') == ['a"b']
    assert parse_csv_line('a"b"') == ['a"b"']


def test_quoted_field_errors():
    with pytest.raises(ValueError):
        parse_csv_line('"unterminated')
    with pytest.raises(ValueError):
        parse_csv_line('"a"x')
    with pytest.raises(ValueError):
        parse_csv_line('"a""')
    # Unterminated quoted field at end of line
    with pytest.raises(ValueError):
        parse_csv_line('",')


def test_unquoted_fields():
    assert parse_csv_line('a,b') == ['a', 'b']
    assert parse_csv_line('abc') == ['abc']
    assert parse_csv_line('a"b') == ['a"b']  # quote inside unquoted field is literal
    assert parse_csv_line('a"b"') == ['a"b"']


def test_edge_cases():
    # Comma-only line: two empty fields
    assert parse_csv_line(',') == ['', '']
    # Unterminated quoted field (quote at start, no closing quote)
    with pytest.raises(ValueError):
        parse_csv_line('",')
