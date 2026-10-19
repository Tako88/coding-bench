"""Tests for solution.evaluate, covering the TASK.md examples and edge cases."""

import unittest

from solution import evaluate


class TestEvaluate(unittest.TestCase):
    # ------------------------------------------------------------------
    # Valid expressions (from the spec's example table)
    # ------------------------------------------------------------------
    def test_example_values(self):
        self.assertEqual(evaluate("1+2*3"), 7.0)
        self.assertEqual(evaluate("2^3^2"), 512.0)
        self.assertEqual(evaluate("-2^2"), -4.0)
        self.assertEqual(evaluate("(-2)^2"), 4.0)
        self.assertEqual(evaluate("(1+2)*3"), 9.0)
        self.assertEqual(evaluate("10/4"), 2.5)
        self.assertEqual(evaluate("1-2-3"), -4.0)
        self.assertEqual(evaluate("8/2/2"), 2.0)
        self.assertEqual(evaluate("2*-3"), -6.0)
        self.assertEqual(evaluate("2--3"), 5.0)
        self.assertEqual(evaluate("2^-3"), 0.125)
        self.assertEqual(evaluate("--3"), 3.0)
        self.assertEqual(evaluate("+3"), 3.0)
        self.assertEqual(evaluate("3.5*2"), 7.0)
        self.assertAlmostEqual(evaluate("2^0.5"), 2.0 ** 0.5)
        self.assertEqual(evaluate("3"), 3.0)
        self.assertEqual(evaluate("( 1 + 2 )"), 3.0)

    def test_result_is_float(self):
        self.assertIs(type(evaluate("3")), float)
        self.assertIs(type(evaluate("10/4")), float)
        self.assertIs(type(evaluate("(1+2)")), float)

    # ------------------------------------------------------------------
    # More valid expressions / edge cases
    # ------------------------------------------------------------------
    def test_additional_valid(self):
        cases = {
            "0.25": 0.25,
            "12": 12.0,
            "0": 0.0,
            "00": 0.0,
            "(-8)^-2": 0.015625,
            "(-8)^2": 64.0,
            "(-8)^2.0": 64.0,
            "(-1)^3": -1.0,
            "1++2": 3.0,          # '+' followed by unary '+'
            "1--2": 3.0,          # '-' followed by unary '-'
            "  1 + 2  ": 3.0,
            "10-2-3": 5.0,
            "2^(1+1)": 4.0,
            "(2^3)^2": 64.0,
            "1.5": 1.5,
            "1^2^3": 1.0,         # right associative: 1^(2^3)
            "5/(1+4)": 1.0,
            "3.14*2": 6.28,
            "((1+2)*3)": 9.0,
            "1000000": 1000000.0,
            "-0.5": -0.5,
            "0^0": 1.0,
            "1.25*8": 10.0,
            "2^-2": 0.25,
            "100/4/5": 5.0,
            "7": 7.0,
        }
        for expr, expected in cases.items():
            self.assertEqual(evaluate(expr), expected, expr)

    def test_fractional_exponent_positive_base(self):
        self.assertAlmostEqual(evaluate("4^0.5"), 2.0)
        self.assertAlmostEqual(evaluate("2^0.25"), 2.0 ** 0.25)

    # ------------------------------------------------------------------
    # Syntax errors -> ValueError
    # ------------------------------------------------------------------
    def test_value_error_cases(self):
        bad = [
            # empty / whitespace-only
            "",
            "   ",
            "\t",
            "\n",
            "1\t+2",
            "1\n2",
            "1\t2",
            # adjacent operands / unbalanced parens
            "1 2",
            "2(3)",
            "(1)2",
            "1)",
            "(",
            "()",
            "(1+2",
            "(1 2)",
            "((",
            "))",
            # dangling / adjacent binary operators
            "1+",
            "2*",
            "3/",
            "4^",
            "+",
            "-",
            "*",
            "/",
            "^",
            "**",
            "1+*2",
            "1-*/2",
            "2^3^",
            # bad numbers
            "1..2",
            "1.",
            ".5",
            ".",
            "1.a",
            "1.2.3",
            # non-allowed characters
            "abc",
            "1e5",
            "1.5e3",
            "1&2",
            "2!",
        ]
        for expr in bad:
            with self.assertRaises(ValueError, msg=repr(expr)):
                evaluate(expr)

    def test_value_error_real_semantics(self):
        for expr in ["(-8)^0.5", "(-8)^(1/2)", "(-8)^0.25"]:
            with self.assertRaises(ValueError, msg=repr(expr)):
                evaluate(expr)

    # ------------------------------------------------------------------
    # Division by zero -> ZeroDivisionError (not ValueError)
    # ------------------------------------------------------------------
    def test_zero_division(self):
        for expr in ["1/0", "0.5/0", "5/(2-2)", "1/(1-1)", "0^-1"]:
            with self.assertRaises(ZeroDivisionError, msg=repr(expr)) as ctx:
                evaluate(expr)
            self.assertNotIsInstance(ctx.exception, ValueError)

    # ------------------------------------------------------------------
    # Overflow -> OverflowError (not ValueError)
    # ------------------------------------------------------------------
    def test_overflow(self):
        for expr in ["2^5^5", "10^400", "999999^999999"]:
            with self.assertRaises(OverflowError, msg=repr(expr)):
                evaluate(expr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
