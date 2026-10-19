"""Tests for solution.py (run with: python3 test_solution.py)."""

import math
import unittest

import solution
from solution import evaluate


class ValueTests(unittest.TestCase):
    """Expressions that must evaluate to a value."""

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
            got = evaluate(expr)
            self.assertEqual(got, expected, expr)
            self.assertIsInstance(got, float, expr)

    def test_extra_values(self):
        cases = [
            ("0", 0.0),
            ("0.25", 0.25),
            ("3.5", 3.5),
            ("  1 ", 1.0),
            ("-8^0.5", -(8.0 ** 0.5)),   # unary binds looser than '^'
            ("-(8)^0.5", -(8.0 ** 0.5)),
            ("2^2^-1", 2.0 ** 0.5),      # 2^(2^-1) = 2^0.5
        ]
        for expr, expected in cases:
            self.assertEqual(evaluate(expr), expected, expr)

    def test_associativity_and_precedence(self):
        self.assertEqual(evaluate("2^2^3"), 256.0)          # right assoc
        self.assertEqual(evaluate("3*(2+1)^2"), 27.0)
        self.assertEqual(evaluate("(3*2)^2"), 36.0)
        self.assertEqual(evaluate("2*3^2"), 18.0)
        self.assertEqual(evaluate("2^2*3"), 12.0)
        self.assertEqual(evaluate("1+2*3+4*5"), 27.0)
        self.assertEqual(evaluate("100/10/5"), 2.0)
        self.assertEqual(evaluate("2-3+4"), 3.0)
        self.assertEqual(evaluate("2^-2^2"), 2.0 ** -4)     # -(2^2) = -4
        self.assertEqual(evaluate("2^-3^2"), 2.0 ** -9)
        self.assertEqual(evaluate("(2^-3)^2"), 2.0 ** -6)
        self.assertEqual(evaluate("+-+3"), -3.0)
        self.assertEqual(evaluate("---3"), -3.0)
        self.assertEqual(evaluate("- 3"), -3.0)
        self.assertEqual(evaluate("-2*-3"), 6.0)
        self.assertEqual(evaluate("-- 2 ^ 2"), 4.0)
        self.assertEqual(evaluate("(-8)^2"), 64.0)
        self.assertEqual(evaluate("(-8)^-2"), 0.015625)
        self.assertEqual(evaluate("(-8)^(4/2)"), 64.0)
        self.assertEqual(evaluate("4^0.5"), 2.0)
        self.assertEqual(evaluate("(0+0)^2"), 0.0)

    def test_nested_parens(self):
        self.assertEqual(evaluate("((((1))))"), 1.0)
        self.assertEqual(evaluate("((1+2)*(3+4))"), 21.0)
        self.assertEqual(evaluate("(1+(2+(3+(4))))"), 10.0)
        self.assertEqual(evaluate("2^(2^(2^2))"), 65536.0)

    def test_whitespace_only_between_tokens(self):
        self.assertEqual(evaluate(" 1 + 2 * 3 "), 7.0)
        self.assertEqual(evaluate("(  ( 1 ) )"), 1.0)
        self.assertEqual(evaluate("1 ^ 2 ^ 2"), 1.0)      # 1^(2^2)
        self.assertEqual(evaluate("2 ^ 2 ^ 2"), 16.0)     # 2^(2^2)
        self.assertEqual(evaluate("1 - - 3"), 4.0)

    def test_return_type_always_float(self):
        for expr in ("3", "1+2", "2^3", "-3", "(3)"):
            self.assertIs(evaluate(expr).__class__, float, expr)


class ErrorTests(unittest.TestCase):
    """Inputs that must raise ValueError."""

    def test_error_examples(self):
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
            "1.5 2",
            "1 2 3",
            "( )",
            "((1+2)",
            "1+2)",
            "1++",
            "1--",
            "1**2",
            "1//2",
            "^^",
            "(",
            ")",
            "1+()",
            "(1+)",
            "(*2)",
            "(1+2))*",
            ".1",
            "..",
            "1.+2",
            "1*2*",
            "-*2",
            "2^-",
            "^2",
            "1 2.5",
            "2 .5",
            "2.5.5",
            "2^",
            "()",
            "1 2",
            "a",
            "1_000",
            "1,5",
            "1 2 ",
            "\t",
            "\n",
            "1 + 2\n",
            "1\t2",
            "\u00a01",       # non-breaking space is not ' '
            "\u0660",        # arabic-indic digit zero is not an ascii digit
            "2**",
            "(-",
            "-",
            "+",
            "1+-",
            "(--)",
            "2^(-)",
        ]
        for expr in bad:
            try:
                got = evaluate(expr)
            except ValueError:
                continue
            raise AssertionError("expected ValueError for %r, got %r" % (expr, got))

    def test_not_zero_division_becomes_value_error(self):
        # Division by zero must propagate as ZeroDivisionError, not ValueError.
        for expr in ("1/0", "0/0", "1/(3-3)", "1/0.0", "5/0^2", "1/(2^0-1)"):
            with self.assertRaises(ZeroDivisionError, msg=expr):
                evaluate(expr)

    def test_overflow(self):
        for expr in ("2^5^5", "10^400", "(9*10)^300", "2^2^10"):
            with self.assertRaises(OverflowError, msg=expr):
                evaluate(expr)

    def test_negative_base_fractional_power(self):
        for expr in ("(-8)^0.5", "(0-8)^0.5", "(-8)^2.5", "(-2)^(1/2)", "(0-2.5)^0.5"):
            with self.assertRaises(ValueError, msg=expr):
                evaluate(expr)
        # legal cases nearby must still work
        self.assertEqual(evaluate("(-8)^-2"), 0.015625)
        self.assertEqual(evaluate("(-8)^2"), 64.0)

    def test_zero_to_negative_power(self):
        # not specified by the task; just make sure it is not silently a
        # ValueError-hiding bug -- python raises ZeroDivisionError here.
        with self.assertRaises(ZeroDivisionError):
            evaluate("0^-1")

    def test_non_string_input(self):
        with self.assertRaises(ValueError):
            evaluate(None)
        with self.assertRaises(ValueError):
            evaluate(3)


class OverflowBoundary(unittest.TestCase):
    def test_large_but_finite(self):
        self.assertEqual(evaluate("2^1023"), 2.0 ** 1023)
        with self.assertRaises(OverflowError):
            evaluate("2^1024")

    def test_underflow_is_fine(self):
        self.assertEqual(evaluate("2^-2000"), 0.0)
        self.assertAlmostEqual(evaluate("2^-1000"), 2.0 ** -1000)


class RandomAgainstPython(unittest.TestCase):
    """Cross-check against python's own arithmetic for a set of safe
    expressions (python uses ** right-assoc too, and unary binds looser than
    ** exactly as in this grammar)."""

    def test_matches_python(self):
        exprs = [
            "1+2*3",
            "2^3^2",
            "(1+2)*3",
            "10/4",
            "1-2-3",
            "8/2/2",
            "2*-3",
            "2--3",
            "2^-3",
            "3.5*2",
            "3*(2+1)^2",
            "2^0.5",
            "(1+2)*(3-4)/(5+6)^2",
            "-2^2",
            "(-2)^2",
            "1+2+3+4+5",
            "((2+3)*(4-1))^2",
        ]
        for e in exprs:
            py = e.replace("^", "**")
            expected = eval(py)
            if isinstance(expected, complex):
                continue
            got = evaluate(e)
            self.assertAlmostEqual(got, expected, msg=e)


if __name__ == "__main__":
    unittest.main(verbosity=1)
