"""Tests for solution.evaluate covering the TASK.md examples and edge cases."""

import random
import re
import unittest

from solution import evaluate


class TestExamples(unittest.TestCase):
    """The examples from TASK.md, verbatim."""

    def test_valid_examples(self):
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

    def test_value_error_examples(self):
        for expr in ["", "   ", "1 2", "1+", "*2", "1+*2", "()", "(1+2",
                     "1)", "1..2", "1.", ".5", "2(3)", "abc", "1\t+2"]:
            with self.subTest(expr=expr):
                with self.assertRaises(ValueError):
                    evaluate(expr)

    def test_runtime_error_examples(self):
        with self.assertRaises(ZeroDivisionError):
            evaluate("1/0")
        with self.assertRaises(OverflowError):
            evaluate("2^5^5")
        with self.assertRaises(ValueError):
            evaluate("(-8)^0.5")

    def test_return_type_is_float(self):
        self.assertIs(evaluate("3").__class__, float)
        for expr in ["1+2", "1/2", "2*3", "-1", "2^3", "0.5"]:
            with self.subTest(expr=expr):
                self.assertIs(evaluate(expr).__class__, float)


class TestSemantics(unittest.TestCase):
    def check(self, expr, expected):
        result = evaluate(expr)
        self.assertIsInstance(result, float)
        self.assertEqual(result, expected,
                         "evaluate(%r) = %r, expected %r"
                         % (expr, result, expected))

    def test_left_associativity(self):
        self.check("1-2-3", -4.0)
        self.check("8/2/2", 2.0)
        self.check("2*3*4", 24.0)
        self.check("100/10/2", 5.0)
        self.check("2-3-4-5", -10.0)
        self.check("10-2-3", 5.0)

    def test_right_associativity_of_power(self):
        self.check("2^3^2", 512.0)
        self.check("2^3^2^1", 512.0)
        self.check("2^(3^2)", 512.0)
        self.check("(2^3)^2", 64.0)
        self.check("2^(3^2)^2", 2.0 ** (9.0 ** 2.0))  # 2^(9^2) = 2^81
        self.check("2^-3^2", 2.0 ** -9.0)             # 2^(-(3^2))
        self.check("2^-2^-1", 2.0 ** -(2.0 ** -1.0))  # 2^(-(2^-1))
        self.check("2^3^2*-2", 512.0 * -2.0)

    def test_precedence(self):
        self.check("1+2*3", 7.0)
        self.check("2*3+4", 10.0)
        self.check("(2+3)*4", 20.0)
        self.check("2^3*2", 16.0)      # (2^3)*2
        self.check("2*3^2", 18.0)      # 2*(3^2)
        self.check("3*(2+1)^2", 27.0)
        self.check("1+2*3^2", 19.0)
        self.check("2-3*2^2", -10.0)
        self.check("2+2*2^2/8-1", 2.0)

    def test_unary(self):
        self.check("-2^2", -4.0)
        self.check("-2^2^2", -16.0)    # -(2^(2^2))
        self.check("--3", 3.0)
        self.check("---3", -3.0)
        self.check("-+3", -3.0)
        self.check("+-3", -3.0)
        self.check("+3", 3.0)
        self.check("2*-3", -6.0)
        self.check("2--3", 5.0)
        self.check("2+-3", -1.0)
        self.check("1++2", 3.0)
        self.check("1*+2", 2.0)
        self.check("2^-3", 0.125)
        self.check("-2^-2", -0.25)     # -(2^-2)
        self.check("2^+3", 8.0)
        self.check("2^-+3", 0.125)
        self.check("2^(-3)", 0.125)
        self.check("- -3", 3.0)
        self.check("- 3", -3.0)
        self.check("2 ^ - 3", 0.125)
        self.check("( -2 )", -2.0)
        self.check("-10+5", -5.0)
        self.check("1 - -2", 3.0)

    def test_numbers(self):
        self.check("3", 3.0)
        self.check("0", 0.0)
        self.check("007", 7.0)
        self.check("0.25", 0.25)
        self.check("0.1+0.2", 0.1 + 0.2)
        self.check("10.0/4", 2.5)
        self.check("1/3", 1.0 / 3.0)
        self.check("7/2", 3.5)
        self.check("0.5*4", 2.0)
        self.check("2^0", 1.0)
        self.check("0^0", 1.0)
        self.check("1^2", 1.0)
        self.check("0^0.5", 0.0)

    def test_whitespace(self):
        self.check("  1 + 2  ", 3.0)
        self.check("( 1 + 2 )", 3.0)
        self.check("(( 1 + 2 ))", 3.0)
        self.check("1 + 2", 3.0)
        self.check(" 1+2 ", 3.0)
        self.check("  -  3  ", -3.0)

    def test_parentheses(self):
        self.check("(1)", 1.0)
        self.check("((1))", 1.0)
        self.check("((((12))))", 12.0)
        self.check("(1+(2))", 3.0)
        self.check("1-(2-3)", 2.0)
        self.check("((1+2)*3)", 9.0)
        self.check("9^(1/2)", 3.0)

    def test_deep_nesting(self):
        for depth in (10, 100, 500):
            expr = "(" * depth + "1" + ")" * depth
            with self.subTest(depth=depth):
                self.check(expr, 1.0)
        self.check("("*200 + "2+2" + ")"*200, 4.0)
        self.check(("1+" * 500) + "1", 501.0)
        self.check(("1-" * 500) + "0", -498.0)

    def test_zero_division(self):
        for expr in ["1/0", "1/(0)", "1/(2-2)", "0/0", "10/(3-3)",
                     "1/(1/0)"]:
            with self.subTest(expr=expr):
                with self.assertRaises(ZeroDivisionError):
                    evaluate(expr)
        # 0 raised to a negative power divides by zero as well
        with self.assertRaises(ZeroDivisionError):
            evaluate("0^-1")
        with self.assertRaises(ZeroDivisionError):
            evaluate("0.0^-1")

    def test_overflow(self):
        for expr in ["2^5^5", "10^10000", "2^1024"]:
            with self.subTest(expr=expr):
                with self.assertRaises(OverflowError):
                    evaluate(expr)
        # just in range
        self.check("2^1023", 2.0 ** 1023.0)
        # a literal too large to be represented as a float
        with self.assertRaises(OverflowError):
            evaluate("9" * 400)
        with self.assertRaises(OverflowError):
            evaluate("9" * 309)
        self.check("9" * 308, float("9" * 308))

    def test_negative_base(self):
        self.check("(-8)^2", 64.0)
        self.check("(-8)^-2", 0.015625)
        self.check("(-8)^3", -512.0)
        self.check("(-8)^0.0", 1.0)
        self.check("(-1)^-1", -1.0)
        self.check("(1-9)^2", 64.0)
        self.check("(1-9)^2.0", 64.0)
        self.check("(1-9)^-2", (1.0 - 9.0) ** -2.0)
        for expr in ["(-8)^0.5", "(-8)^1.5", "(1-9)^0.5",
                     "(1-9)^1.25"]:
            with self.subTest(expr=expr):
                with self.assertRaises(ValueError):
                    evaluate(expr)

    def test_invalid_input(self):
        bad = [
            # empty / whitespace only
            "", " ", "   ", "\t", "\n", "\t1", "1\t2", "1\n+2",
            # illegal characters
            "abc", "a", "1e5", "1,2", "1;2", "1@2", "2.5f",
            # operators in an operand position
            "*2", "/2", "^2", "1+*2", "1-/*2", "1/**2", "1^^2", "1^*2",
            "1+^2", "2 3^", "1 -", "1 ^", "1 *", "1 /", "1+", "1^",
            "1*", "1/", "-", "+", "*", "/", "^", "--", "++", "1++",
            "2^3^", "-- 3 ^",
            # operands in an operator position / adjacency
            "1 2", "1 2 3", "2 3", "0 0", "1 1 1", "2(3)", "1(2)",
            "1 ( 2 )", "(1)(2)", "(1+2)(3+4)", "2(3)4", "1+2)3",
            "(1+2)3",
            # unbalanced or empty parentheses
            "()", "(())", "1))", "())", "(1+2", "1)", "(1+2))",
            "(1+2 3", "(1 2)", "( -", "(-)",
            # malformed numbers
            "1..2", "1.", ".5", "0.", "5.", "1.2.3", "0.5.5",
            "3 . 5", "1 . 2",
        ]
        for expr in bad:
            with self.subTest(expr=expr):
                with self.assertRaises(ValueError):
                    evaluate(expr)

    def test_non_string_input(self):
        for value in (None, 42, 3.5, b"1+2", ["1"], ("1",)):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    evaluate(value)


class TestAgainstPython(unittest.TestCase):
    """Randomized expressions: the spec's precedence/associativity match
    Python's, so Python's own parser can serve as an oracle."""

    OPS = ["+", "-", "*", "/", "^"]

    def _gen(self, rng, depth):
        choice = rng.random()
        if depth <= 1 or choice < 0.35:
            if rng.random() < 0.25:
                return "%d.%d" % (rng.randint(1, 9), rng.randint(0, 9))
            return str(rng.randint(1, 9))
        if choice < 0.55:
            return "(" + self._gen(rng, depth - 1) + ")"
        if choice < 0.9:
            left = self._gen(rng, depth - 1)
            op = rng.choice(self.OPS)
            if op == "^":
                right = str(rng.randint(1, 3))
            else:
                right = self._gen(rng, depth - 1)
            return left + op + right
        # unary prefix (signs bind looser than '^', like in the spec)
        return rng.choice(["-", "+", "", "--"]) + self._gen(rng, depth - 1)

    @staticmethod
    def _float_oracle(expr):
        # Python mirrors the spec's float arithmetic if every literal is
        # forced to be a float ('^' maps to '**', same precedence/associativity
        # and unary-minus binding as the grammar).
        forced = re.sub(r"\d+\.?\d*", lambda m: repr(float(m.group(0))), expr)
        return eval(forced.replace("^", "**"))

    def test_random_expressions(self):
        rng = random.Random(20240521)
        for i in range(600):
            expr = self._gen(rng, 4)
            try:
                expected = self._float_oracle(expr)
            except ZeroDivisionError:
                with self.assertRaises(ZeroDivisionError):
                    evaluate(expr)
                continue
            with self.subTest(expr=expr, i=i):
                result = evaluate(expr)
                self.assertIsInstance(result, float)
                self.assertEqual(result, expected)

    def test_random_zero_division(self):
        rng = random.Random(99)
        for i in range(100):
            s = str(rng.randint(1, 9))
            expr = "%d/(%s-%s)" % (rng.randint(1, 9), s, s)
            with self.subTest(expr=expr):
                with self.assertRaises(ZeroDivisionError):
                    evaluate(expr)

    def test_random_overflow(self):
        big = ["2^3^3^2", "3^3^3^2", "2^2^3^4", "9^3^3^2"]
        for base in big:
            for tail in big:
                expr = "%s^%s" % (base, tail)  # definitely out of range
                with self.subTest(expr=expr):
                    with self.assertRaises(OverflowError):
                        evaluate(expr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
