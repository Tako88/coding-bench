import math
import unittest

from solution import evaluate


def approx(a, b):
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


class TestExamples(unittest.TestCase):
    def check(self, expr, expected):
        result = evaluate(expr)
        self.assertIsInstance(result, float)
        self.assertTrue(approx(result, expected),
                        "%r -> %r, expected %r" % (expr, result, expected))

    def test_basic(self):
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

    def test_float_result(self):
        self.assertEqual(evaluate("2^0.5"), 2.0 ** 0.5)
        self.assertEqual(evaluate("3").__class__, float)


class TestErrors(unittest.TestCase):
    def check_value(self, expr):
        with self.assertRaises(ValueError):
            evaluate(expr)

    def test_errors(self):
        self.check_value("")
        self.check_value("   ")
        self.check_value("1 2")
        self.check_value("1+")
        self.check_value("*2")
        self.check_value("1+*2")
        self.check_value("()")
        self.check_value("(1+2")
        self.check_value("1)")
        self.check_value("1..2")
        self.check_value("1.")
        self.check_value(".5")
        self.check_value("2(3)")
        self.check_value("abc")
        self.check_value("1\t+2")
        self.check_value("2\t3")
        self.check_value("1\n+2")


class TestSpecial(unittest.TestCase):
    def test_div_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            evaluate("1/0")

    def test_overflow(self):
        with self.assertRaises(OverflowError):
            evaluate("2^5^5")

    def test_negative_base_fractional_exp(self):
        with self.assertRaises(ValueError):
            evaluate("(-8)^0.5")

    def test_negative_base_integral_exp(self):
        self.assertEqual(evaluate("(-8)^2"), 64.0)

    def test_negative_exponent(self):
        self.assertEqual(evaluate("(-8)^-2"), 0.015625)


if __name__ == "__main__":
    unittest.main()
