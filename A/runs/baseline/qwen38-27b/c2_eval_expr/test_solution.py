"""Tests for solution.evaluate (arithmetic expression evaluator).

Run:  python3 test_solution.py
"""

import math
from solution import evaluate

_failures = []


def ok(name, cond):
    if not cond:
        _failures.append("FAIL %s" % name)
    return cond


def check_value(name, expr, expected):
    """expect evaluate(expr) == expected (exact)"""
    try:
        r = evaluate(expr)
    except Exception as e:  # noqa: BLE001
        _failures.append("FAIL %s: raised %s: %s" % (name, type(e).__name__, e))
        return
    if not isinstance(r, float):
        _failures.append("FAIL %s: result %r is not a float" % (name, r))
        return
    if r != expected:
        _failures.append("FAIL %s: %r != %r" % (name, r, expected))


def check_approx(name, expr, expected, tol=1e-9):
    try:
        r = evaluate(expr)
    except Exception as e:  # noqa: BLE001
        _failures.append("FAIL %s: raised %s: %s" % (name, type(e).__name__, e))
        return
    if not (abs(r - expected) <= tol):
        _failures.append("FAIL %s: %r not close to %r" % (name, r, expected))


def check_raises(name, expr, exc):
    try:
        r = evaluate(expr)
    except exc:
        return
    except Exception as e:  # noqa: BLE001
        _failures.append(
            "FAIL %s: raised %s, expected %s"
            % (name, type(e).__name__, exc.__name__))
        return
    _failures.append(
        "FAIL %s: returned %r, expected %s" % (name, r, exc.__name__))


# ---------------------------------------------------------------- examples --

def test_examples():
    check_value("ex 1+2*3", "1+2*3", 7.0)
    check_value("ex 2^3^2", "2^3^2", 512.0)
    check_value("ex -2^2", "-2^2", -4.0)
    check_value("ex (-2)^2", "(-2)^2", 4.0)
    check_value("ex (1+2)*3", "(1+2)*3", 9.0)
    check_value("ex 10/4", "10/4", 2.5)
    check_value("ex 1-2-3", "1-2-3", -4.0)
    check_value("ex 8/2/2", "8/2/2", 2.0)
    check_value("ex 2*-3", "2*-3", -6.0)
    check_value("ex 2--3", "2--3", 5.0)
    check_value("ex 2^-3", "2^-3", 0.125)
    check_value("ex --3", "--3", 3.0)
    check_value("ex +3", "+3", 3.0)
    check_value("ex 3.5*2", "3.5*2", 7.0)
    check_value("ex 2^0.5", "2^0.5", 2.0 ** 0.5)
    check_value("ex 3", "3", 3.0)
    check_value("ex ( 1 + 2 )", "( 1 + 2 )", 3.0)

    check_raises("ex empty", "", ValueError)
    check_raises("ex spaces only", "   ", ValueError)
    check_raises("ex 1 2", "1 2", ValueError)
    check_raises("ex 1+", "1+", ValueError)
    check_raises("ex *2", "*2", ValueError)
    check_raises("ex 1+*2", "1+*2", ValueError)
    check_raises("ex ()", "()", ValueError)
    check_raises("ex (1+2", "(1+2", ValueError)
    check_raises("ex 1)", "1)", ValueError)
    check_raises("ex 1..2", "1..2", ValueError)
    check_raises("ex 1.", "1.", ValueError)
    check_raises("ex .5", ".5", ValueError)
    check_raises("ex 2(3)", "2(3)", ValueError)
    check_raises("ex abc", "abc", ValueError)
    check_raises("ex tab", "1\t+2", ValueError)
    check_raises("ex 1/0", "1/0", ZeroDivisionError)
    check_raises("ex 2^5^5", "2^5^5", OverflowError)
    check_raises("ex (-8)^0.5", "(-8)^0.5", ValueError)


# ----------------------------------------------------------------- values --

def test_return_type():
    r = evaluate("3")
    ok("3 is exactly 3.0", r == 3.0)
    ok("class of result is float", type(r) is float)


def test_return_class():
    for e in ["1+1", "10/4", "2^0.5", "-3", "1.5"]:
        r = evaluate(e)
        ok("class(%s)" % e, type(r) is float)


def test_precedence_and_associativity():
    check_value("1+2*3=7", "1+2*3", 7.0)
    check_value("(1+2)*3=9", "(1+2)*3", 9.0)
    check_value("3*4+5=17", "3*4+5", 17.0)
    check_value("3+4*5=23", "3+4*5", 23.0)
    check_value("2^3^2=512", "2^3^2", 512.0)
    check_value("3*(2+1)^2=27", "3*(2+1)^2", 27.0)
    check_value("2*3^2=18", "2*3^2", 18.0)
    check_value("3^2*2=18", "3^2*2", 18.0)
    check_value("16/2^3=2", "16/2^3", 2.0)
    check_value("2^3/2=4", "2^3/2", 4.0)
    check_value("1-2-3=-4", "1-2-3", -4.0)
    check_value("8/2/2=2", "8/2/2", 2.0)
    check_value("10-3-2=5", "10-3-2", 5.0)
    check_value("100/10/2=5", "100/10/2", 5.0)
    check_value("2*3*4=24", "2*3*4", 24.0)
    check_value("24/2*3=36", "24/2*3", 36.0)
    check_value("1+2+3+4=10", "1+2+3+4", 10.0)
    check_value("2^3^2^1=512", "2^3^2^1", 512.0)
    check_value("2^(1+1)^2=16", "2^(1+1)^2", 16.0)
    check_value("2^2^3=256", "2^2^3", 256.0)
    check_value("4^0.5=2", "4^0.5", 2.0)
    check_value("8^2", "8^2", 64.0)
    check_value("2*2^2=8", "2*2^2", 8.0)


def test_unary():
    check_value("-2^2=-4", "-2^2", -4.0)
    check_value("--3=3", "--3", 3.0)
    check_value("+-3=-3", "+-3", -3.0)
    check_value("-+3=-3", "-+3", -3.0)
    check_value("++3=3", "++3", 3.0)
    check_value("++-3=-3", "++-3", -3.0)
    check_value("--2^2=4", "--2^2", 4.0)
    check_value("2*-3=-6", "2*-3", -6.0)
    check_value("2--3=5", "2--3", 5.0)
    check_value("2+-3=-1", "2+-3", -1.0)
    check_value("2--3*2=11", "2--3*2", 11.0)
    check_value("2^-3=0.125", "2^-3", 0.125)
    check_value("-3^2=-9", "-3^2", -9.0)
    check_value("-2^-2=0.25", "-2^-2", 0.25)
    check_value("(-2)^2=4", "(-2)^2", 4.0)
    check_value("(-2)^-2=0.25", "(-2)^-2", 0.25)
    check_value("(-4)^-2=0.0625", "(-4)^-2", 0.0625)
    check_value("2^-2^2=0.0625", "2^-2^2", 0.0625)
    check_value("1^-2^2=1", "1^-2^2", 1.0)
    check_value("-2^-1=-0.5", "-2^-1", -0.5)
    check_value("10--5=15", "10--5", 15.0)
    check_value("5--3*2=11", "5--3*2", 11.0)
    check_value("8/-2=-4", "8/-2", -4.0)
    check_value("-(2+3)=-5", "-(2+3)", -5.0)
    check_value("-(2)^2=-4", "-(2)^2", -4.0)
    check_value("-( -2 )^2=-4", "-( -2 )^2", -4.0)


def test_numbers():
    check_value("3=3.0", "3", 3.0)
    check_value("0=0.0", "0", 0.0)
    check_value("007=7", "007", 7.0)
    check_value("3.5", "3.5", 3.5)
    check_value("0.25", "0.25", 0.25)
    check_value("123.456", "123.456", 123.456)
    check_value("3.5*2=7", "3.5*2", 7.0)
    check_value("0.5*4=2", "0.5*4", 2.0)
    check_value("10/4=2.5", "10/4", 2.5)
    check_value("1.5+1.5=3", "1.5+1.5", 3.0)
    check_value("1.5^2=2.25", "1.5^2", 2.25)
    check_value("2.5^2=6.25", "2.5^2", 6.25)
    check_value("2^1.0=2", "2^1.0", 2.0)
    check_value("2^-0.5", "2^-0.5", 2.0 ** -0.5)
    check_value("0.1*10=1", "0.1*10", 1.0)
    check_value("100-0.1", "100-0.1", 100 - 0.1)
    check_value("999999999", "999999999", 999999999.0)
    check_value("int exact then float", "123456789*1000000", 123456789.0e6)


def test_spaces():
    check_value("space around op", "1 + 2", 3.0)
    check_value("many spaces", "  1   +   2  ", 3.0)
    check_value("( 1 + 2 )", "( 1 + 2 )", 3.0)
    check_value("space before unary", "2 * - 3", -6.0)
    check_value("space around ^", "2 ^ 3", 8.0)
    check_value("spaces in exponent", "2 ^ - 3", 0.125)
    check_value("space between signs", "- - 3", 3.0)
    check_value("space after open paren", "( 1 )", 1.0)
    check_raises("tab between ops", "1 \t+ 2", ValueError)
    check_raises("newline", "1\n+2", ValueError)
    check_raises("newline in expr", "1 +\n2", ValueError)
    check_raises("tab around", "\t1\t", ValueError)
    check_raises("carriage return", "1\r", ValueError)


def test_power_semantics():
    # integer-valued float exponent is fine on a negative base
    check_value("(-8)^2.0=64", "(-8)^2.0", 64.0)
    check_value("(-8)^-2=1/64", "(-8)^-2", 1.0 / 64.0)
    check_value("(-8)^-1=-0.125", "(-8)^-1", -0.125)
    check_value("(-1)^3=-1", "(-1)^3", -1.0)
    check_value("(-2)^3=-8", "(-2)^3", -8.0)
    check_value("(-1)^2=1", "(-1)^2", 1.0)
    check_value("2^-3=1/8", "2^-3", 1.0 / 8.0)
    check_value("2^0.5=sqrt2", "2^0.5", math.sqrt(2.0))
    check_value("4^-0.5=0.5", "4^-0.5", 0.5)
    check_value("1^1000000=1", "1^1000000", 1.0)
    check_value("5^0=1", "5^0", 1.0)
    check_value("0^5=0", "0^5", 0.0)
    check_value("0^0=1 (python)", "0^0", 1.0)
    # negative base with fractional exponent is an error
    check_raises("(-8)^0.5", "(-8)^0.5", ValueError)
    check_raises("(-8)^1.5", "(-8)^1.5", ValueError)
    check_raises("(-1)^0.5", "(-1)^0.5", ValueError)
    check_raises("(-8)^-0.5", "(-8)^-0.5", ValueError)
    check_raises("(-4)^2.5", "(-4)^2.5", ValueError)
    # float negative base too
    check_raises("(-8.0)^0.5", "(-8.0)^0.5", ValueError)
    check_value("(-8.0)^2=64", "(-8.0)^2", 64.0)


def test_zero_division():
    check_raises("1/0", "1/0", ZeroDivisionError)
    check_raises("1/0.0", "1/0.0", ZeroDivisionError)
    check_raises("1.0/0", "1.0/0", ZeroDivisionError)
    check_raises("1.0/0.0", "1.0/0.0", ZeroDivisionError)
    check_raises("0/0", "0/0", ZeroDivisionError)
    check_raises("1/(2-2)", "1/(2-2)", ZeroDivisionError)
    check_raises("10/(5-5)", "10/(5-5)", ZeroDivisionError)
    # zero ** negative power also divides by zero
    check_raises("0^-1", "0^-1", ZeroDivisionError)
    check_raises("0^-0.5", "0^-0.5", ZeroDivisionError)
    # zero ** 0 and zero ** positive are fine
    check_value("0^0=1", "0^0", 1.0)
    check_value("0^1=0", "0^1", 0.0)


def test_overflow():
    check_raises("2^5^5", "2^5^5", OverflowError)
    check_raises("2^(5^5)", "2^(5^5)", OverflowError)
    check_raises("10^10000", "10^10000", OverflowError)
    check_raises("(10^10)^1000", "(10^10)^1000", OverflowError)
    check_raises("-(2^5^5)", "-(2^5^5)", OverflowError)
    # but these fit in a float
    check_value("9^9=387420489", "9^9", 387420489.0)
    check_value("9^18", "9^18", 9.0 ** 18)
    check_value("10^308 fits", "10^308", 1e308)


def test_errors():
    # empty / whitespace only
    check_raises("empty", "", ValueError)
    check_raises("one space", " ", ValueError)
    check_raises("spaces", "   ", ValueError)
    check_raises("tab only", "\t", ValueError)
    check_raises("newline only", "\n", ValueError)
    # bad characters
    check_raises("abc", "abc", ValueError)
    check_raises("1a", "1a", ValueError)
    check_raises("a1", "a1", ValueError)
    check_raises("1&2", "1&2", ValueError)
    check_raises("1==2", "1==2", ValueError)
    check_raises("1<2", "1<2", ValueError)
    check_raises("2**3 (star)", "2**3", ValueError)
    check_raises("2==3", "2==3", ValueError)
    check_raises("2;3", "2;3", ValueError)
    check_raises("2,3", "2,3", ValueError)
    check_raises("hex 0x1", "0x1", ValueError)
    check_raises("percent", "1%", ValueError)
    # bad structure
    check_raises("1 2", "1 2", ValueError)
    check_raises("1 2 3", "1 2 3", ValueError)
    check_raises("2(3)", "2(3)", ValueError)
    check_raises("(3)2", "(3)2", ValueError)
    check_raises("1+2 3", "1+2 3", ValueError)
    check_raises("1+2*3 4", "1+2*3 4", ValueError)
    check_raises("()", "()", ValueError)
    check_raises("((1))", "((1))", 1.0)  # placeholder, replaced below
    # unbalanced parens
    check_raises("(1+2", "(1+2", ValueError)
    check_raises("1+2)", "1+2)", ValueError)
    check_raises("1)", "1)", ValueError)
    check_raises("(1)", "(1)", 1.0)  # valid; checked by value below
    check_raises("((1+2", "((1+2", ValueError)
    check_raises("1+2))", "1+2))", ValueError)
    check_raises("(1+2)(", "(1+2)(", ValueError)
    check_raises("()()", "()()", ValueError)
    # dangling operators
    check_raises("1+", "1+", ValueError)
    check_raises("1-", "1-", ValueError)
    check_raises("1*", "1*", ValueError)
    check_raises("1/", "1/", ValueError)
    check_raises("1^", "1^", ValueError)
    check_raises("1+-", "1+-", ValueError)
    check_raises("1^-", "1^-", ValueError)
    check_raises("*2", "*2", ValueError)
    check_raises("+2+", "+2+", ValueError)
    check_raises("1+*2", "1+*2", ValueError)
    check_raises("1+/-2", "1+/-2", 1.0 - (-2.0))  # valid; checked below
    check_raises("1*+*2", "1*+*2", ValueError)
    check_raises("**1", "**1", ValueError)
    check_raises("+-*1", "+-*1", ValueError)
    check_raises("1^^2", "1^^2", ValueError)
    check_raises("1^-^2", "1^-^2", ValueError)
    check_raises("(+)", "(+)", ValueError)
    check_raises("(-)", "(-)", ValueError)
    check_raises("(*)", "(*)", ValueError)
    check_raises("(^)", "(^)", ValueError)
    check_raises("(- +)", "(- +)", ValueError)
    # bad numbers
    check_raises("1.", "1.", ValueError)
    check_raises(".5", ".5", ValueError)
    check_raises("1..2", "1..2", ValueError)
    check_raises("1.2.3", "1.2.3", ValueError)
    check_raises(".5.5", ".5.5", ValueError)
    check_raises("1.", "1.", ValueError)
    check_raises("+.5", "+.5", ValueError)
    check_raises("-(.)", "-(.)", ValueError)
    check_raises("1.+2", "1.+2", ValueError)
    check_raises("1.2e3", "1.2e3", ValueError)
    check_raises("e3", "e3", ValueError)
    # trailing garbage
    check_raises("1 2 3 x", "1 2 3 x", ValueError)
    check_raises("12x", "12x", ValueError)


def test_valid_nesting():
    check_value("((1+2))", "((1+2))", 3.0)
    check_value("((1))", "((1))", 1.0)
    check_value("(1+2)(3)", "(1+2)(3)", 9.0 if False else None)  # invalid!
    check_value("1*(2)", "1*(2)", 2.0)
    check_value("2/(1/2)", "2/(1/2)", 4.0)
    check_value("((2^3)^2)", "((2^3)^2)", 64.0)
    check_value("(1+(2*(3+4)))", "(1+(2*(3+4)))", 15.0)
    check_value("(2+3)*(4+5)", "(2+3)*(4+5)", 45.0)
    check_value("1/(1/(1+2))", "1/(1/(1+2))", 3.0)


def test_misc():
    check_value("single 0", "0", 0.0)
    check_value("0+0", "0+0", 0.0)
    check_value("0*5", "0*5", 0.0)
    check_value("0^1", "0^1", 0.0)
    check_value("big ints exact", "123456789*987654321",
               float(123456789 * 987654321))
    check_value("chained", "1+2*3-4/2^2", 1 + 2 * 3 - float(4 / 2 ** 2))
    check_value("deep", "1+2*3-4/2^2+5-6/3", 1 + 2 * 3 - float(4 / 2 ** 2)
               + 5 - float(6 / 3))
    check_value("sqrt via pow", "81^0.5", 9.0)
    check_value("cube root approx", "8^(1/3)", 8.0 ** (1.0 / 3.0))
    check_value("0.5^2=0.25", "0.5^2", 0.25)
    check_value("(-0.5)^2=0.25", "(-0.5)^2", 0.25)
    check_value("long number", "123456789012345678",
               123456789012345678.0)
    check_value("spaces everywhere", "  1  +  2  *  3  ", 7.0)


def main():
    test_examples()
    test_return_type()
    test_return_class()
    test_precedence_and_associativity()
    test_unary()
    test_numbers()
    test_spaces()
    test_power_semantics()
    test_zero_division()
    test_overflow()
    test_errors()
    test_valid_nesting()
    test_misc()
    if _failures:
        print("\n".join(_failures))
        print("FAILED: %d test(s) failed" % len(_failures))
        raise SystemExit(1)
    print("All tests passed.")


if __name__ == "__main__":
    main()
