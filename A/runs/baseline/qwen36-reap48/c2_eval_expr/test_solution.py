"""Tests for solution.py - arithmetic expression evaluator."""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from solution import evaluate


def test_basic_examples():
    """Test all the examples from TASK.md."""
    # Basic arithmetic
    assert evaluate("1+2*3") == 7.0, f"1+2*3 = {evaluate('1+2*3')}"
    assert evaluate("2^3^2") == 512.0, f"2^3^2 = {evaluate('2^3^2')}"
    assert evaluate("-2^2") == -4.0, f"-2^2 = {evaluate('-2^2')}"
    assert evaluate("(-2)^2") == 4.0, f"(-2)^2 = {evaluate('(-2)^2')}"
    assert evaluate("(1+2)*3") == 9.0, f"(1+2)*3 = {evaluate('(1+2)*3')}"
    assert evaluate("10/4") == 2.5, f"10/4 = {evaluate('10/4')}"
    assert evaluate("1-2-3") == -4.0, f"1-2-3 = {evaluate('1-2-3')}"
    assert evaluate("8/2/2") == 2.0, f"8/2/2 = {evaluate('8/2/2')}"

    # Unary
    assert evaluate("2*-3") == -6.0, f"2*-3 = {evaluate('2*-3')}"
    assert evaluate("2--3") == 5.0, f"2--3 = {evaluate('2--3')}"
    assert evaluate("2^-3") == 0.125, f"2^-3 = {evaluate('2^-3')}"
    assert evaluate("--3") == 3.0, f"--3 = {evaluate('--3')}"
    assert evaluate("+3") == 3.0, f"+3 = {evaluate('+3')}"

    # Decimals
    assert evaluate("3.5*2") == 7.0, f"3.5*2 = {evaluate('3.5*2')}"
    assert abs(evaluate("2^0.5") - (2.0**0.5)) < 1e-15, f"2^0.5 = {evaluate('2^0.5')}"

    # Simple
    assert evaluate("3") == 3.0, f"3 = {evaluate('3')}"
    assert evaluate("( 1 + 2 )") == 3.0, f"( 1 + 2 ) = {evaluate('( 1 + 2 )')}"


def test_return_type():
    """Return value is always float."""
    assert isinstance(evaluate("3"), float)
    assert isinstance(evaluate("1+2"), float)
    assert isinstance(evaluate("3.5"), float)


def test_errors():
    """Test error cases from TASK.md."""
    # Empty string
    try:
        evaluate("")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Whitespace-only
    try:
        evaluate("   ")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Two operands adjacent
    try:
        evaluate("1 2")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Trailing operator
    try:
        evaluate("1+")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Leading binary operator
    try:
        evaluate("*2")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Two binary operators adjacent
    try:
        evaluate("1+*2")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Empty parens
    try:
        evaluate("()")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Unbalanced parens
    try:
        evaluate("(1+2")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    try:
        evaluate("1)")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Invalid number formats
    try:
        evaluate("1..2")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    try:
        evaluate("1.")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    try:
        evaluate(".5")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Operand followed by paren
    try:
        evaluate("2(3)")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Non-numeric characters
    try:
        evaluate("abc")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Tab character
    try:
        evaluate("1\t+2")
        assert False, "Should raise ValueError"
    except ValueError:
        pass

    # Division by zero -> ZeroDivisionError
    try:
        evaluate("1/0")
        assert False, "Should raise ZeroDivisionError"
    except ZeroDivisionError:
        pass

    # Overflow
    try:
        evaluate("2^5^5")
        assert False, "Should raise OverflowError"
    except OverflowError:
        pass

    # Negative base with fractional exponent
    try:
        evaluate("(-8)^0.5")
        assert False, "Should raise ValueError"
    except ValueError:
        pass


def test_edge_cases():
    """Additional edge cases following the grammar."""
    # Negative base with integral exponent (should work)
    assert evaluate("(-8)^2") == 64.0

    # Negative base with negative integer exponent
    # Grammar: -8^-2 = -(8^(-2)) = -(1/64) = -0.015625
    assert abs(evaluate("-8^-2") - (-0.015625)) < 1e-10

    # Multiple unary signs
    assert evaluate("---3") == -3.0
    assert evaluate("----3") == 3.0

    # Complex expressions
    assert evaluate("2*3+4*5") == 26.0
    assert evaluate("10/2*3") == 15.0  # Left-associative: (10/2)*3
    assert evaluate("2*3^2") == 18.0  # ^ binds tighter: 2*(3^2)

    # Spaces in various positions
    assert evaluate(" 1 + 2 ") == 3.0
    assert evaluate("1  +  2") == 3.0

    # Deeply nested
    assert evaluate("((1+2)*3)") == 9.0
    assert evaluate("(((3)))") == 3.0

    # Parenthesized expression with unary
    assert evaluate("(-2)^3") == -8.0
    assert evaluate("(-2)^3^2") == -512.0  # (-2)^(3^2) = (-2)^9 = -512

    # Right associativity of ^
    assert evaluate("2^3^2") == 512.0  # 2^(3^2) = 2^9 = 512

    # Complex mix
    assert evaluate("1+2*3^2") == 19.0  # 1+(2*(3^2)) = 1+18 = 19

    # Decimal numbers
    assert evaluate("0.25") == 0.25
    assert evaluate("1.5+2.5") == 4.0


def test_tab_in_middle():
    """Tab anywhere should be an error."""
    try:
        evaluate("1+2\t+3")
        assert False, "Should raise ValueError"
    except ValueError:
        pass


def test_special_invalid_chars():
    """Various invalid characters."""
    for ch in ['!', '@', '#', '$', '%', '&', '_', '{', '}', '[', ']']:
        try:
            evaluate(f"1{ch}2")
            assert False, f"Should raise ValueError for {ch!r}"
        except ValueError:
            pass


def test_negative_base_integral_exp():
    """Negative base with integral exponent should work."""
    assert evaluate("(-8)^2") == 64.0
    assert evaluate("(-2)^3") == -8.0
    assert evaluate("(-3)^3") == -27.0


def test_3_times_2_plus_1_squared():
    """3*(2+1)^2 = 27 from the grammar description."""
    assert evaluate("3*(2+1)^2") == 27.0


if __name__ == "__main__":
    test_basic_examples()
    print("test_basic_examples PASSED")

    test_return_type()
    print("test_return_type PASSED")

    test_errors()
    print("test_errors PASSED")

    test_edge_cases()
    print("test_edge_cases PASSED")

    test_tab_in_middle()
    print("test_tab_in_middle PASSED")

    test_special_invalid_chars()
    print("test_special_invalid_chars PASSED")

    test_negative_base_integral_exp()
    print("test_negative_base_integral_exp PASSED")

    test_3_times_2_plus_1_squared()
    print("test_3_times_2_plus_1_squared PASSED")

    print("\nAll tests passed!")
