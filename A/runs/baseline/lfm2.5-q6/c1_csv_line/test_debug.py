import pytest
from solution import parse_csv_line

def test_debug():
    try:
        parse_csv_line('",')
    except ValueError as e:
        print("CAUGHT:", e)
        raise
    else:
        print("NO EXCEPTION")
