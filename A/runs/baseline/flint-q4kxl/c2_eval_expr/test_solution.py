import math
import unittest

from solution import evaluate


class TestEvaluate(unittest.TestCase):
    def test_examples(self):
        cases = [
            ("1+2*3", 7.0),
            ("2^3^2", 512.0),
            ("-2^2", -4.0),
            ("(-2)^2", 4.0),
            ("(1+2)*3", 9.0),
            ("10/4", 2.5),
            ("1-2-3", -4.0),
            ("8/2/2", 2.0),
            ("2*-3", -6.0),
            ("2--3", 5.0),
            ("2^-3", 0.125),
            ("--3", 3.0),
            ("+3", 3.0),
            ("3.5*2", 7.0),
            ("2^0.5", 2.0 ** 0.5),
            ("3", 3.0),
            ("( 1 + 2 )", 3.0),
        ]
        for expr, expected in cases:
            with self.subTest(expr=expr):
                self.assertEqual(evaluate(expr), expected)

    def test_result_is_float(self):
        self.assertIsInstance(evaluate("3"), float)
        self.assertEqual(evaluate("3"), 3.0)

    def test_decimal_numbers(self):
        self.assertEqual(evaluate("0.25"), 0.25)
        self.assertEqual(evaluate("12.5+0.5"), 13.0)
        self.assertEqual(evaluate("3.5*2"), 7.0)

    def test_power_edges(self):
        self.assertEqual(evaluate("2^0"), 1.0)
        self.assertEqual(evaluate("2^-2"), 0.25)
        self.assertEqual(evaluate("2^2.0"), 4.0)
        self.assertEqual(evaluate("3*(2+1)^2"), 27.0)
        self.assertEqual(evaluate("(-2)^3"), -8.0)

    def test_left_associativity(self):
        self.assertEqual(evaluate("1-2-3"), -4.0)
        self.assertEqual(evaluate("8/2/2"), 2.0)
        self.assertEqual(evaluate("2*3/4"), 1.5)

    def test_syntax_errors(self):
        bad = [
            "",
            "   ",
            "1 2",
            "1+",
            "*2",
            "1+*2",
            "()",
            "(1+2",
            "1)",
            "1..2",
            "1.",
            ".5",
            "2(3)",
            "abc",
            "1\t+2",
            "1\n+2",
            "5 5",
            "((1)",
            "1++",
            "1*/2",
            "2^^3",
            "1.2.3",
            "1 + ",
            "()1",
            "2^",
            "0x10",
            "1e5",
        ]
        for expr in bad:
            with self.subTest(expr=expr):
                with self.assertRaises(ValueError):
                    evaluate(expr)

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            evaluate("1/0")

    def test_negative_base_fractional_exponent(self):
        with self.assertRaises(ValueError):
            evaluate("(-8)^0.5")

    def test_overflow(self):
        with self.assertRaises(OverflowError):
            evaluate("2^5^5")

    def test_negative_base_integral_exponent(self):
        self.assertEqual(evaluate("(-8)^2"), 64.0)
        self.assertEqual(evaluate("(-8)^-2"), 0.015625)


if __name__ == "__main__":
    unittest.main()
