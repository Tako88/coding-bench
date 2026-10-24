import math
import unittest

from solution import evaluate


class Base(unittest.TestCase):
    def check(self, expr, expected):
        result = evaluate(expr)
        self.assertIsInstance(result, float, "%r did not return float" % expr)
        self.assertTrue(math.isclose(result, expected, rel_tol=1e-12,
                                     abs_tol=1e-12),
                        "%r -> %r, expected %r" % (expr, result, expected))

    def check_value_error(self, expr):
        with self.assertRaises(ValueError):
            evaluate(expr)


class ValidCases(Base):
    def test_examples(self):
        self.check("1+2*3", 7.0)
        self.check("2^3^2", 512.0)
        self.check("-2^2", -4.0)
        self.check("(-2)^2", 4.0)
        self.check("(1+2)*3", 9.0)
        self.check("10/4", 2.5)
        self.check("1-2-3", -4.0)
        self.check("8/2/2", 2.0)
        self.check("2*-3", -6.0)
        self.check("2--3", 5.0)
        self.check("2^-3", 0.125)
        self.check("--3", 3.0)
        self.check("+3", 3.0)
        self.check("3.5*2", 7.0)
        self.check("3", 3.0)
        self.check("( 1 + 2 )", 3.0)

    def test_type_float(self):
        self.assertIsInstance(evaluate("3"), float)

    def test_fractional_exponent(self):
        self.check("2^0.5", 2.0 ** 0.5)
        self.check("0.25", 0.25)
        self.check("12", 12.0)

    def test_right_assoc_power(self):
        self.check("2^3^2", 512.0)
        self.check("3*(2+1)^2", 27.0)

    def test_repeated_unary(self):
        self.check("---3", -3.0)
        self.check("++3", 3.0)

    def test_negative_exponent_integral(self):
        self.check("-8^-2", -(8 ** -2))  # grammar: -(8^-2)
        self.check("(-8)^2", 64.0)

    def test_negative_base_integral_exp(self):
        self.check("(-2)^3", -8.0)

    def test_deeply_nested(self):
        self.check("((1))", 1.0)
        self.check("(((2+3))*4)", 20.0)


class ErrorCases(Base):
    def test_empty_and_whitespace(self):
        self.check_value_error("")
        self.check_value_error("   ")
        # leading/trailing spaces are fine -> valid
        self.check(" 1 ", 1.0)

    def test_adjacent_operands(self):
        self.check_value_error("1 2")
        self.check_value_error("2(3)")

    def test_bad_syntax(self):
        for expr in ["1+", "*2", "1+*2", "()", "(1+2", "1)", "1..2",
                     "1.", ".5", "abc", "2(3)"]:
            self.check_value_error(expr)

    def test_tab(self):
        self.check_value_error("1\t+2")
        self.check_value_error("\t1+2")
        self.check_value_error("1+2\t")

    def test_invalid_chars(self):
        self.check_value_error("1&2")
        self.check_value_error("1.2.3")
        self.check_value_error("()()")

    def test_unbalanced(self):
        self.check_value_error("(1+2")
        self.check_value_error("1)2")


class SpecialErrors(unittest.TestCase):
    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            evaluate("1/0")
        with self.assertRaises(ZeroDivisionError):
            evaluate("5/2/0")

    def test_overflow(self):
        with self.assertRaises(OverflowError):
            evaluate("2^5^5")

    def test_negative_base_fractional(self):
        with self.assertRaises(ValueError):
            evaluate("(-8)^0.5")
        with self.assertRaises(ValueError):
            evaluate("(-2)^0.5")
        # unary minus outside the power does not make the base negative:
        # -2^0.5 == -(2^0.5) is a perfectly valid float.
        self.assertAlmostEqual(evaluate("-2^0.5"), -(2.0 ** 0.5))


if __name__ == "__main__":
    unittest.main()
