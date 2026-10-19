import sys
from solution import evaluate

def test(expr, expected):
    try:
        result = evaluate(expr)
        if isinstance(expected, type) and issubclass(expected, Exception):
            print(f"FAIL: {expr!r} expected {expected.__name__} but got {result}")
            sys.exit(1)
        else:
            if result == expected:
                print(f"PASS: {expr!r} -> {result}")
            else:
                print(f"FAIL: {expr!r} -> {result}, expected {expected}")
                sys.exit(1)
    except Exception as e:
        if isinstance(expected, type) and isinstance(e, expected):
            print(f"PASS: {expr!r} raised {expected.__name__}")
        else:
            print(f"FAIL: {expr!r} expected {expected.__name__} but got {type(e).__name__}: {e}")
            sys.exit(1)

# Test cases from TASK.md examples
test("1+2*3", 7.0)
test("2^3^2", 512.0)
test("-2^2", -4.0)
test("(-2)^2", 4.0)  # Note: (-2)^2 should be 4.0, but our parser currently may not handle parentheses with unary minus inside? Actually (-2)^2 is valid: primary '(' expr ')' where expr is -2. Our parser should handle it.
test("(1+2)*3", 9.0)
test("10/4", 2.5)
test("1-2-3", -4.0)
test("8/2/2", 2.0)
test("2*-3", -6.0)
test("2--3", 5.0)
test("2^-3", 0.125)
test("--3", 3.0)
test("+3", 3.0)
test("3.5*2", 7.0)
test("2^0.5", 2.0**0.5)  # approx sqrt(2)
test("3", 3.0)
test("( 1 + 2 )", 3.0)

# Error cases
test("", ValueError)
test("   ", ValueError)
test("1 2", ValueError)
test("1+", ValueError)
test("*2", ValueError)
test("1+*2", ValueError)
test("()", ValueError)
test("(1+2", ValueError)
test("1)", ValueError)
test("1..2", ValueError)
test("1.", ValueError)
test(".5", ValueError)
test("2(3)", ValueError)
test("abc", ValueError)
test("1\t+2", ValueError)  # tab not allowed
test("1/0", ZeroDivisionError)
test("2^5^5", OverflowError)
test("(-8)^0.5", ValueError)

print("All tests passed!")