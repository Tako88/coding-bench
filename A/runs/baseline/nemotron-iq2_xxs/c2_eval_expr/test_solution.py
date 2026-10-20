import solution


def check(expr, expected):
    result = solution.evaluate(expr)
    if not isinstance(result, float):
        raise AssertionError("%r: expected float, got %r" % (expr, type(result)))
    if result != expected:
        raise AssertionError("%r: expected %r, got %r" % (expr, expected, result))


def expect_value_error(expr):
    try:
        solution.evaluate(expr)
    except ValueError:
        return
    raise AssertionError("%r: expected ValueError" % (expr,))


# Examples from the task
check("1+2*3", 7.0)
check("2^3^2", 512.0)
check("-2^2", -4.0)
check("(-2)^2", 4.0)
check("(1+2)*3", 9.0)
check("10/4", 2.5)
check("1-2-3", -4.0)
check("8/2/2", 2.0)
check("2*-3", -6.0)
check("2--3", 5.0)
check("2^-3", 0.125)
check("--3", 3.0)
check("+3", 3.0)
check("3.5*2", 7.0)
check("2^0.5", 2.0 ** 0.5)
check("3", 3.0)
check("( 1 + 2 )", 3.0)

# Return type is always float
assert isinstance(solution.evaluate("3"), float)
assert solution.evaluate("3") == 3.0

# Syntax errors
for bad in ["", "   ", "1 2", "1+", "*2", "1+*2", "()", "(1+2", "1)",
            "1..2", "1.", ".5", "2(3)", "abc", "1\t+2", "1.2.3", "1+2+",
            "(1+2))", "((1+2", "2^", "-", "+", "()()", "1 2 3"]:
    expect_value_error(bad)

# Division by zero propagates
try:
    solution.evaluate("1/0")
    raise AssertionError("1/0: expected ZeroDivisionError")
except ZeroDivisionError:
    pass

# Overflow propagates
try:
    solution.evaluate("2^5^5")
    raise AssertionError("2^5^5: expected OverflowError")
except OverflowError:
    pass

# Negative base to fractional exponent is an error
try:
    solution.evaluate("(-8)^0.5")
    raise AssertionError("(-8)^0.5: expected ValueError")
except ValueError:
    pass

# Negative base with integral exponent is fine
check("(-8)^2", 64.0)
check("(-8)^-2", 0.015625)
check("-8^-2", -0.015625)

# Right associativity of ^
check("3*(2+1)^2", 27.0)

# Repeated unary operators
check("++3", 3.0)
check("+-3", -3.0)
check("-+-3", 3.0)
check("-+-+-3", -3.0)

# Unary after binary operators
check("2+-3", -1.0)
check("2-+-3", 5.0)

# Nested parentheses
check("((1+2)*(3+4))", 21.0)
check("((((3))))", 3.0)

# Decimals
check("0.25", 0.25)
check("1.5/2", 0.75)
check("2^0.5", 2.0 ** 0.5)

# No tabs/newlines anywhere
expect_value_error("1\n+2")
expect_value_error("1\t+2")
expect_value_error("+\n2")

print("all tests passed")
