import sys
import math
sys.path.insert(0, '.')
from solution import evaluate


def test_examples():
    # Basic examples from the spec
    assert evaluate("1+2*3") == 7.0
    assert evaluate("2^3^2") == 512.0
    assert evaluate("-2^2") == -4.0
    assert evaluate("(-2)^2") == 4.0
    assert evaluate("(1+2)*3") == 9.0
    assert evaluate("10/4") == 2.5
    assert evaluate("1-2-3") == -4.0
    assert evaluate("8/2/2") == 2.0
    assert evaluate("2*-3") == -6.0
    assert evaluate("2--3") == 5.0
    assert evaluate("2^-3") == 0.125
    assert evaluate("--3") == 3.0
    assert evaluate("+3") == 3.0
    assert evaluate("3.5*2") == 7.0
    assert evaluate("2^0.5") == 2.0**0.5
    assert evaluate("3") == 3.0
    assert evaluate("( 1 + 2 )") == 3.0


def test_empty_and_whitespace():
    # Empty string should raise ValueError
    try:
        evaluate("")
        assert False, "Expected ValueError for empty string"
    except ValueError:
        pass

    # Whitespace-only string should raise ValueError
    try:
        evaluate("   ")
        assert False, "Expected ValueError for whitespace-only string"
    except ValueError:
        pass


def test_invalid_inputs():
    # Adjacent operands
    try:
        evaluate("1 2")
        assert False, "Expected ValueError for adjacent operands"
    except ValueError:
        pass

    # Adjacent binary operators
    try:
        evaluate("1+*2")
        assert False, "Expected ValueError for adjacent binary operators"
    except ValueError:
        pass

    # Trailing operator
    try:
        evaluate("1+")
        assert False, "Expected ValueError for trailing operator"
    except ValueError:
        pass

    # Unmatched parentheses
    try:
        evaluate("(1+2")
        assert False, "Expected ValueError for unmatched open paren"
    except ValueError:
        pass

    try:
        evaluate("1)")
        assert False, "Expected ValueError for trailing close paren"
    except ValueError:
        pass

    # Invalid number formats
    try:
        evaluate("1.")
        assert False, "Expected ValueError for number without fractional digits"
    except ValueError:
        pass

    try:
        evaluate(".5")
        assert False, "Expected ValueError for number without integer digits"
    except ValueError:
        pass

    try:
        evaluate("1..2")
        assert False, "Expected ValueError for double dot"
    except ValueError:
        pass

    # Invalid characters
    try:
        evaluate("abc")
        assert False, "Expected ValueError for non-numeric string"
    except ValueError:
        pass

    try:
        evaluate("1\t+2")
        assert False, "Expected ValueError for tab character"
    except ValueError:
        pass


def test_division_by_zero():
    # Division by zero should raise ZeroDivisionError (not ValueError)
    try:
        evaluate("1/0")
        assert False, "Expected ZeroDivisionError for division by zero"
    except ZeroDivisionError:
        pass


def test_overflow():
    # 2^5^5 overflows
    try:
        evaluate("2^5^5")
        assert False, "Expected OverflowError for 2^5^5"
    except OverflowError:
        pass


def test_negative_fractional_exponent():
    # Negative base with fractional exponent is an error
    try:
        evaluate("(-8)^0.5")
        assert False, "Expected ValueError for negative base fractional exponent"
    except ValueError:
        pass

    # Negative exponent is fine: (-8)^-2 = 0.015625
    assert evaluate("(-8)^-2") == 0.015625

    # Negative base with integral exponent is fine: (-8)^2 = 64
    assert evaluate("(-8)^2") == 64.0


def test_unary_operators():
    # Multiple unary plus/minus
    assert evaluate("---5") == -5.0
    assert evaluate("++5") == 5.0
    assert evaluate("-+5") == -5.0
    assert evaluate("--+5") == 5.0


def test_right_associativity():
    # Right associativity of ^: 2^3^2 = 512
    assert evaluate("2^3^2") == 512.0


def test_left_associativity():
    # Left associativity: 1-2-3 = -4
    assert evaluate("1-2-3") == -4.0
    assert evaluate("8/2/2") == 2.0


if __name__ == "__main__":
    test_examples()
    test_empty_and_whitespace()
    test_invalid_inputs()
    test_division_by_zero()
    test_overflow()
    test_negative_fractional_exponent()
    test_unary_operators()
    test_right_associativity()
    test_left_associativity()
    print("All tests passed!")
