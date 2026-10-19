"""Hidden tests for benchmark C. Never shown to the model.

Usage:  python3 checks.py <task_id> <path/to/solution.py>
Prints one JSON object: {"ok": bool, "detail": str}

The task ids are c1_csv_line, c2_eval_expr, c3_tokenize, c4_schedule,
c5_shortest_match.

Fixed cases come from the task spec. Random cases are checked against a
brute-force oracle (_oracle.py), so a candidate cannot pass by matching one
hand-picked example. Every performance gate in the spec is enforced here, and
the whole check is wrapped in an alarm so a hanging candidate cannot block the
harness.
"""

import importlib.util
import json
import os
import random
import signal
import sys
import time

from _oracle import (
    brute_schedule,
    brute_shortest,
    ref_evaluate,
    ref_schedule,
    ref_shortest,
    ref_tokenize,
)


class CheckFail(Exception):
    pass


class Timeout(BaseException):
    """BaseException so a broad 'except Exception' in a candidate cannot swallow it."""


def _on_alarm(signum, frame):
    raise Timeout()


signal.signal(signal.SIGALRM, _on_alarm)

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------ performance gates
# A performance gate is not an absolute number of seconds. The same correct
# solution costs ~0.5s on one machine and ~4s on another, so an absolute budget
# fails the slower one for no reason. Every gate here is therefore a multiple of
# what the bundled reference solution costs on the machine doing the grading.
# `checks.py --calibrate` times the references and prints calibration.json;
# BENCH_CALIBRATION points at that file. Without it the absolute fallbacks are
# used and every verdict says "no calibration" rather than pretending.
GATE_MULTIPLES = {
    "c3_200k_line": 6.0,
    "c4_200k_intervals": 6.0,
    "c4_200k_identical": 6.0,
    "c5_20_stars": 4.5,
}
# GATE_FLOOR is the absolute budget this suite shipped with. A calibrated budget
# is never below it, so a machine *faster* than the reference is not graded more
# harshly than the original suite was, and a gate whose reference is tiny (c3's
# 200k line is 0.02s) stays a check on algorithmic complexity rather than on
# timer noise.
GATE_FLOOR = {
    "c3_200k_line": 3.0,
    "c4_200k_intervals": 3.0,
    "c4_200k_identical": 3.0,
    "c5_20_stars": 10.0,
}

CALIBRATION = {}
GATE_TIMES = {}
C3_BUDGET = GATE_FLOOR["c3_200k_line"]
C4_BUDGET = GATE_FLOOR["c4_200k_intervals"]
C4_IDENT_BUDGET = GATE_FLOOR["c4_200k_identical"]
STAR_BUDGET = GATE_FLOOR["c5_20_stars"]
STAR_LIMIT = 40.0


def _load_calibration():
    path = os.environ.get("BENCH_CALIBRATION")
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return {}


def gate_budget(label):
    """The calibrated budget in seconds, or the absolute floor."""
    entry = CALIBRATION.get("gates", {}).get(label) or {}
    val = entry.get("budget_seconds")
    if isinstance(val, (int, float)) and val > 0:
        return float(val)
    return GATE_FLOOR[label]


def gate_label(label, dt):
    """'in 0.52s (0.99x ref, budget 6.0x = 3.00s)', or the uncalibrated form."""
    entry = CALIBRATION.get("gates", {}).get(label) or {}
    ref = entry.get("ref_seconds")
    if isinstance(ref, (int, float)) and ref > 0:
        return "in %.2fs (%.2fx ref, budget %.1fx = %.2fs)" % (
            dt, dt / ref, entry.get("multiple", GATE_MULTIPLES[label]), gate_budget(label))
    return "in %.2fs (no calibration; absolute budget %.2fs)" % (dt, gate_budget(label))


def gate_record(label, dt):
    """Remember a measured gate time so --calibrate can read it back."""
    GATE_TIMES[label] = dt
    return dt


def _apply_calibration():
    global CALIBRATION, C3_BUDGET, C4_BUDGET, C4_IDENT_BUDGET, STAR_BUDGET, STAR_LIMIT
    CALIBRATION = _load_calibration()
    C3_BUDGET = gate_budget("c3_200k_line")
    C4_BUDGET = gate_budget("c4_200k_intervals")
    C4_IDENT_BUDGET = gate_budget("c4_200k_identical")
    STAR_BUDGET = gate_budget("c5_20_stars")
    STAR_LIMIT = max(40.0, STAR_BUDGET * 2.0)


_apply_calibration()


class time_limit(object):
    def __init__(self, seconds, label):
        self.seconds = seconds
        self.label = label
        self.prev = None

    def __enter__(self):
        self.prev = signal.setitimer(signal.ITIMER_REAL, self.seconds)
        return self

    def __exit__(self, exc_type, exc, tb):
        signal.setitimer(signal.ITIMER_REAL, *(self.prev if self.prev else (0, 0)))
        if exc_type is Timeout:
            raise CheckFail("%s did not finish within %.1fs" % (self.label, self.seconds))
        return False


def load(path):
    spec = importlib.util.spec_from_file_location("candidate_module", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def eq(got, want, label):
    if got != want:
        raise CheckFail("%s: got %r, want %r" % (label, got, want))


def close(got, want, label, tol=1e-6):
    if isinstance(got, int) and isinstance(want, int) and not isinstance(got, bool):
        if got != want:
            raise CheckFail("%s: got %r, want %r" % (label, got, want))
        return
    try:
        g, w = float(got), float(want)
    except Exception:
        raise CheckFail("%s: got %r, want a number near %r" % (label, got, want))
    if abs(g - w) > tol * max(1.0, abs(w)):
        raise CheckFail("%s: got %r, want %r" % (label, got, want))


def raises(fn, label):
    try:
        fn()
    except ValueError:
        return
    except Timeout:
        raise
    except Exception as e:
        raise CheckFail("%s: raised %s instead of ValueError" % (label, type(e).__name__))
    raise CheckFail("%s: no ValueError raised" % label)


def as_pair(v):
    if not isinstance(v, (tuple, list)) or len(v) != 2:
        raise CheckFail("result must be a (total_profit, chosen) pair, got %r" % (v,))
    prof, chosen = v
    if isinstance(chosen, (str, bytes)) or not isinstance(chosen, (tuple, list)):
        raise CheckFail("chosen must be a list of intervals, got %r" % (chosen,))
    out = []
    for item in chosen:
        if isinstance(item, (str, bytes)) or not isinstance(item, (tuple, list)) or len(item) != 3:
            raise CheckFail("each chosen interval must be a (start, end, profit) triple, got %r" % (item,))
        vals = []
        for x in item:
            if isinstance(x, bool) or not isinstance(x, int):
                raise CheckFail("interval fields must be ints, got %r" % (item,))
            vals.append(int(x))
        out.append(tuple(vals))
    if out != sorted(out):
        raise CheckFail("chosen intervals must be ordered by (start, end, profit), got %r" % (out,))
    if isinstance(prof, bool) or not isinstance(prof, int):
        try:
            prof = int(prof)
        except Exception:
            raise CheckFail("total_profit must be an int, got %r" % (prof,))
    return (int(prof), out)


# ---------------------------------------------------------------- c1


def c1(mod):
    f = mod.parse_csv_line
    eq(f("a,b,c"), ["a", "b", "c"], "simple")
    eq(f("a"), ["a"], "single field")
    eq(f("a,,b"), ["a", "", "b"], "empty field")
    eq(f(",,,"), ["", "", "", ""], "only commas")
    eq(f(""), [""], "empty line")
    eq(f('""'), [""], "empty quoted field")
    eq(f('a,"b"'), ["a", "b"], "quoted second field")
    eq(f(',"a"'), ["", "a"], "quoted field after a comma")
    eq(f('"a",'), ["a", ""], "trailing comma after a quoted field")
    eq(f('"a,b",c'), ["a,b", "c"], "comma in quotes")
    eq(f('"a b"'), ["a b"], "space in quotes")
    eq(f('","'), [","], "only a quoted comma")
    eq(f('"he said ""hi""",x'), ['he said "hi"', "x"], "escaped quotes")
    eq(f('""""'), ['"'], "quoted escaped quote")
    eq(f('a"b'), ['a"b'], "quote inside unquoted field")
    eq(f('a"b"'), ['a"b"'], "two quotes inside unquoted field")
    eq(f('a,"b,c",d'), ["a", "b,c", "d"], "quoted middle field")
    raises(lambda: f('"unterminated'), "unterminated quote")
    raises(lambda: f('"a"x'), "text after closing quote")
    raises(lambda: f('"a""'), "escaped quote then end of line")
    raises(lambda: f('a,"b"x'), "text after closing quote mid line")

    # Round trip: build a record from random fields, render it per the spec, and
    # require the parsed fields back. The expected value comes from the generator,
    # not from the reference parser.
    rng = random.Random(20260101)
    alphabet = ["a", "b", "c", ",", '"', " ", ";", "'"]
    for _ in range(400):
        fields = []
        for _ in range(rng.randint(1, 5)):
            fields.append("".join(rng.choice(alphabet) for _ in range(rng.randint(0, 6))))
        parts = []
        for s in fields:
            if s == "" or "," in s or '"' in s:
                parts.append('"' + s.replace('"', '""') + '"')
            else:
                parts.append(s)
        line = ",".join(parts)
        eq(f(line), fields, "round trip %r" % (line,))
    return "fixed + 400 round trips"


# ---------------------------------------------------------------- c2


def c2(mod):
    g = mod.evaluate
    close(g("1+2*3"), 7.0, "precedence")
    close(g("2^3^2"), 512.0, "right associative power")
    close(g("-2^2"), -4.0, "unary minus binds looser than power")
    close(g("(-2)^2"), 4.0, "parenthesised negative base")
    close(g("(1+2)*3"), 9.0, "parentheses")
    close(g("10/4"), 2.5, "division")
    close(g("1-2-3"), -4.0, "left associative minus")
    close(g("8/2/2"), 2.0, "left associative division")
    close(g("2*-3"), -6.0, "unary after binary")
    close(g("2--3"), 5.0, "binary minus then unary minus")
    close(g("2^-3"), 0.125, "unary exponent")
    close(g("--3"), 3.0, "double unary minus")
    close(g("+3"), 3.0, "unary plus")
    close(g("3.5*2"), 7.0, "decimal literal")
    close(g("0.25*4"), 1.0, "decimal literal with leading zero")
    close(g("007"), 7.0, "leading zeros")
    close(g("2^0.5"), 2.0 ** 0.5, "fractional exponent")
    close(g("3*(2+1)^2"), 27.0, "mixed")
    close(g("-(1+2)"), -3.0, "unary on parentheses")
    close(g(" 1 + 2 "), 3.0, "spaces")
    close(g("3"), 3.0, "bare integer")
    if not isinstance(g("3"), float):
        raise CheckFail("evaluate must return a float, got %r" % (g("3"),))
    raises(lambda: g(""), "empty string")
    raises(lambda: g("   "), "spaces only")
    raises(lambda: g("1 2"), "two operands")
    raises(lambda: g("1+"), "trailing operator")
    raises(lambda: g("*2"), "leading binary operator")
    raises(lambda: g("1+*2"), "two binary operators")
    raises(lambda: g("()"), "empty parentheses")
    raises(lambda: g("(1+2"), "unbalanced open")
    raises(lambda: g("1)"), "unbalanced close")
    raises(lambda: g("1..2"), "double dot")
    raises(lambda: g("1."), "trailing dot")
    raises(lambda: g(".5"), "leading dot")
    raises(lambda: g("2(3)"), "two operands")
    raises(lambda: g("abc"), "letters")
    raises(lambda: g("1\t+2"), "tab")
    raises(lambda: g("1e5"), "exponent letter")
    try:
        g("1/0")
    except ZeroDivisionError:
        pass
    except Exception as e:
        raise CheckFail("1/0: raised %s instead of ZeroDivisionError" % type(e).__name__)
    else:
        raise CheckFail("1/0: no ZeroDivisionError raised")
    try:
        g("2^5^5")
    except OverflowError:
        pass
    except Exception as e:
        raise CheckFail("2^5^5: raised %s instead of OverflowError" % type(e).__name__)
    else:
        raise CheckFail("2^5^5: no OverflowError raised")

    raises(lambda: g("(-8)^0.5"), "negative base, fractional exponent")

    # Random expressions against Python itself as the oracle ('^' -> '**' is a
    # faithful translation: both are right associative and bind tighter than
    # unary minus and than * /).
    rng = random.Random(7)
    checked = 0
    for _ in range(600):
        src = _gen_expr(rng)
        try:
            want = float(eval(src.replace("^", "**"), {"__builtins__": {}}, {}))
            want_err = None
        except BaseException as e:
            want = None
            want_err = type(e)
        try:
            got = mod.evaluate(src)
            got_err = None
        except Timeout:
            raise
        except BaseException as e:
            got = None
            got_err = type(e)
        if want_err is not None:
            if got_err is not want_err:
                raise CheckFail("%r: oracle raised %s, candidate %s"
                                % (src, want_err.__name__, got_err.__name__ if got_err else "nothing"))
            continue
        if got_err is not None:
            raise CheckFail("%r: candidate raised %s, oracle says %r"
                            % (src, got_err.__name__, want))
        close(got, want, "random %r" % (src,))
        checked += 1
    return "fixed + %d random expressions" % checked


def _gen_expr(rng, depth=3):
    r = rng.random()
    if depth <= 0 or r < 0.22:
        return _gen_num(rng)
    r = rng.random()
    if r < 0.16:
        return rng.choice(["-", "+", "--", "-+"]) + _gen_expr(rng, depth - 1)
    if r < 0.36:
        return "(" + _gen_expr(rng, depth - 1) + ")"
    if r < 0.42:
        return _gen_small(rng) + "^" + _gen_small(rng)
    if r < 0.62:
        return _gen_expr(rng, depth - 1) + rng.choice(["+", "-"]) + _gen_expr(rng, depth - 1)
    if r < 0.85:
        return _gen_expr(rng, depth - 1) + rng.choice(["*", "/"]) + _gen_expr(rng, depth - 1)
    return _gen_small(rng) + "^" + _gen_small(rng) + rng.choice(["*", "+", "-"]) + _gen_num(rng)


def _gen_num(rng):
    r = rng.random()
    if r < 0.6:
        return str(rng.randint(0, 99))
    return "%d.%d" % (rng.randint(0, 20), rng.randint(1, 99))


def _gen_small(rng):
    return str(rng.randint(2, 5))


# ---------------------------------------------------------------- c3


def c3(mod):
    f = mod.tokenize
    cases = [
        (["a", "b", "c"], "a b c"),
        (["a", "b"], "a    b"),
        ([], ""),
        ([], "   \t  "),
        (["--version"], "--version"),
        (["its"], "'it''s'"),
        (["ab"], "a''b"),
        (["", ""], "'' ''"),
        (["", "a"], '"" a'),
        (["ab cd"], 'a"b c"d'),
        (["ab", "cd"], 'a"b" "c"d'),
        (["-xy z"], '-x"y z"'),
        (["a b"], "a\\ b"),
        (["#a"], "\\#a"),
        (["a#b"], "a#b"),
        (["a"], "a #b"),
        ([], "#a"),
        (["a#b#c"], "a#b#c"),
        (['a"b'], '"a\\"b"'),
        (["a\\b"], '"a\\\\b"'),
        (["a\\qb"], '"a\\qb"'),
        (["a\\b"], "'a\\b'"),
        ([""], '""'),
        ([""], "''"),
        (["a", ""], "a ''"),
        (["#", "a"], "\\# a"),
        (["a b", "c"], '"a b" c'),
        (["", ""], "\"\" ''"),
        (["x"], "x"),
        (["\\"], "\\\\"),
        (["'"], "\\'"),
        (['"'], '\'"\''),
        (["a", "b"], "a\tb"),
    ]
    for want, line in cases:
        eq(f(line), want, "tokenize(%r)" % (line,))
    for bad in ["a\\", "'abc", '"abc', "a 'b", 'a "b']:
        raises(lambda b=bad: f(b), "tokenize(%r)" % (bad,))

    # Generated round trip: render random tokens into a line whose token list is
    # known by construction, including empty segments and comments.
    rng = random.Random(99)
    pool = "abxy09,;#'\"\\-+="
    for _ in range(500):
        want = []
        parts = []
        for _ in range(rng.randint(1, 4)):
            tok = "".join(rng.choice(pool) for _ in range(rng.randint(0, 5)))
            want.append(tok)
            parts.append(_render_token(rng, tok))
        line = ""
        for k, part in enumerate(parts):
            if k:
                line += rng.choice([" ", "\t", "  "])
            line += part
        if rng.random() < 0.25:
            line += rng.choice([" ", "\t"]) + "#" + "".join(
                rng.choice(pool) for _ in range(rng.randint(0, 4)))
        elif rng.random() < 0.25:
            line = rng.choice([" ", "\t"]) + line
        eq(f(line), want, "generated %r" % (line,))

    line = 'a"b c"d ' * 25000
    with time_limit(max(4.0, C3_BUDGET * 1.25), "200k character line"):
        t0 = time.perf_counter()
        out = f(line)
        dt = time.perf_counter() - t0
    if len(out) != 25000 or out[0] != "ab cd" or out[-1] != "ab cd":
        raise CheckFail("200k line: got %d tokens starting %r" % (len(out), out[:1]))
    gate_record("c3_200k_line", dt)
    if dt > C3_BUDGET:
        raise CheckFail("200k character line took %.2fs, budget is %.2fs" % (dt, C3_BUDGET))
    return "fixed + 500 generated + 200k %s" % gate_label("c3_200k_line", dt)


def _render_token(rng, tok):
    """Render tok as one shell token: any mixture of segments, value preserved."""
    pieces = []
    # random segmentation, including empty chunks
    i = 0
    while i < len(tok):
        k = rng.randint(1, max(1, len(tok) - i))
        pieces.append(tok[i:i + k])
        i += k
    if not pieces or rng.random() < 0.3:
        pieces.insert(rng.randint(0, len(pieces)), "")
    if rng.random() < 0.3:
        pieces.append("")
    if tok == "" and not pieces:
        pieces = [""]
    out = []
    for chunk in pieces:
        form = rng.choice(["single", "double", "bare"])
        if chunk == "":
            form = rng.choice(["single", "double"])
        if form == "single" and "'" not in chunk:
            out.append("'" + chunk + "'")
        elif form == "double":
            out.append('"' + chunk.replace("\\", "\\\\").replace('"', '\\"') + '"')
        else:
            buf = []
            for ch in chunk:
                if ch in " \t#'\"\\":
                    buf.append("\\" + ch)
                else:
                    buf.append(ch)
            out.append("".join(buf))
    return "".join(out)


# ---------------------------------------------------------------- timing helper

MARGIN = 0.15  # within 15% of a budget -> report the result as "marginal"


def best_of_limit(fn, budget, attempts=3, limit=20.0, what="gate"):
    """Time fn() up to `attempts` times and keep the best.

    A single sample at a budget edge flips on scheduler noise: the same
    c4_schedule solution graded at 3.00s (pass) and then 3.03/3.05/3.08/3.16/
    3.18/3.23s (fail) across repeated runs of an identical file. The criterion
    is unchanged -- the BEST sample must still fit the budget -- but a
    borderline implementation is now judged on the algorithm rather than on one
    unlucky schedule, and a result this close to the edge is labelled.

    Returns (value, best_seconds, all_samples, marginal).
    """
    times = []
    value = None
    for _ in range(attempts):
        with time_limit(limit, what):
            t0 = time.perf_counter()
            value = fn()
            times.append(time.perf_counter() - t0)
        if times[-1] <= budget:
            break  # a pass is a pass; no need to sample again
    best = min(times)
    return value, best, times, (best <= budget and best > budget * (1.0 - MARGIN))


def _fmt_times(times):
    return ", ".join("%.2f" % t for t in times)


# ---------------------------------------------------------------- c4


def c4(mod):
    cases = [
        ((0, []), []),
        ((5, [(0, 3, 5)]), [(0, 3, 5)]),
        ((7, [(0, 5, 3), (5, 10, 4)]), [(0, 5, 3), (5, 10, 4)]),
        ((8, [(0, 5, 4), (5, 10, 4)]), [(0, 5, 4), (5, 10, 4), (0, 10, 7)]),
        ((10, [(0, 10, 10)]), [(0, 5, 5), (5, 10, 5), (0, 10, 10)]),
        ((10, [(0, 10, 10)]), [(0, 10, 10), (1, 2, 1)]),
        ((4, [(5, 6, 2), (8, 10, 2)]), [(8, 10, 2), (5, 6, 2)]),
        ((10, [(0, 2, 5), (2, 8, 5)]), [(4, 8, 5), (0, 4, 5), (2, 8, 5), (0, 2, 5)]),
        ((10, [(0, 1, 5), (1, 2, 5)]), [(0, 1, 5), (1, 2, 5), (0, 2, 5)]),
        ((20, [(0, 2, 10), (2, 4, 10)]), [(0, 2, 10), (1, 3, 1), (2, 4, 10)]),
        ((2, [(0, 1, 1), (1, 2, 1)]), [(0, 1, 1), (1, 2, 1), (0, 1, 1), (1, 2, 1)]),
        ((3, [(0, 1, 1), (1, 2, 1), (2, 3, 1)]), [(0, 1, 1), (1, 2, 1), (2, 3, 1)]),
        ((6, [(2, 5, 6)]), [(0, 4, 3), (2, 5, 6)]),
        ((14, [(0, 1, 2), (1, 3, 9), (3, 4, 3)]), [(0, 1, 2), (1, 3, 9), (3, 4, 3)]),
    ]
    for want, ivs in cases:
        got = as_pair(mod.best_schedule(list(ivs)))
        eq(got, want, "best_schedule(%r)" % (ivs,))

    rng = random.Random(4242)
    for _ in range(120):
        ivs = []
        for _ in range(rng.randint(0, 9)):
            s = rng.randint(0, 8)
            e = s + rng.randint(1, 4)
            ivs.append((s, e, rng.randint(1, 6)))
        got = as_pair(mod.best_schedule(list(ivs)))
        eq(got, brute_schedule(ivs), "random %r" % (ivs,))

    big = []
    for _ in range(200000):
        s = rng.randint(0, 1000000)
        big.append((s, s + rng.randint(1, 500), rng.randint(1, 1000)))
    want = ref_schedule(big)
    alarm = max(20.0, C4_BUDGET * 1.5)
    got, dt, times, marginal = best_of_limit(
        lambda: as_pair(mod.best_schedule(list(big))), C4_BUDGET,
        limit=alarm, what="200k intervals")
    eq(got, want, "200k random intervals")
    gate_record("c4_200k_intervals", dt)
    if dt > C4_BUDGET:
        raise CheckFail("200k intervals took %.2fs (best of %s), budget is %.2fs"
                        % (dt, _fmt_times(times), C4_BUDGET))

    ident = [(0, 1, 1)] * 200000
    got2, dt2, times2, marginal2 = best_of_limit(
        lambda: as_pair(mod.best_schedule(list(ident))), C4_IDENT_BUDGET,
        limit=alarm, what="200k identical intervals")
    eq(got2, (1, [(0, 1, 1)]), "200k identical intervals")
    gate_record("c4_200k_identical", dt2)
    if dt2 > C4_IDENT_BUDGET:
        raise CheckFail("200k identical intervals took %.2fs (best of %s), budget is %.2fs"
                        % (dt2, _fmt_times(times2), C4_IDENT_BUDGET))
    note = ""
    if marginal or marginal2:
        note = (" [marginal: random best %.2fs of %s, identical best %.2fs of %s, budget %.2fs]"
                % (dt, _fmt_times(times), dt2, _fmt_times(times2), C4_BUDGET))
    return "fixed + 120 brute-checked + 200k %s%s" % (gate_label("c4_200k_intervals", dt), note)


# ---------------------------------------------------------------- c5


def c5(mod):
    f = mod.shortest_prefix_match
    cases = [
        (3, ("abc", "abcdef")),
        (3, ("a*c", "abcde")),
        (0, ("*", "abc")),
        (0, ("*", "")),
        (1, ("a*", "a")),
        (4, ("*b", "aaab")),
        (2, ("**b", "ab")),
        (2, ("{ab,cd}", "cdx")),
        (3, ("{a,ab}c", "abc")),
        (2, ("{*,a}b", "ab")),
        (2, ("{,a}b", "ab")),
        (0, ("{}", "ab")),
        (3, ("a?c", "abcd")),
        (3, ("a\\*b", "a*bc")),
        (-1, ("a", "")),
        (-1, ("abc", "ab")),
        (0, ("", "abc")),
        (1, ("?", "a")),
        (0, ("{a,}", "")),
        (3, ("{a,?b}c", "abc")),
        (2, ("*?b", "ab")),
        (5, ("a*e", "abcde")),
        (2, ("\\{a", "{ab")),
        (1, ("{,*}b", "b")),
    ]
    for want, (pat, text) in cases:
        eq(f(pat, text), want, "shortest_prefix_match(%r, %r)" % (pat, text))
    for bad in [("a\\", "a"), ("{a,b", "ab"), ("a}b", "ab"), ("{a,{b}c", "abc")]:
        raises(lambda b=bad: f(*b), "shortest_prefix_match(%r)" % (bad,))

    rng = random.Random(31337)
    for _ in range(250):
        pat = _gen_pattern(rng)
        text = "".join(rng.choice("abc") for _ in range(rng.randint(0, 9)))
        try:
            want = brute_shortest(pat, text)
            bad = None
        except ValueError as e:
            want = None
            bad = str(e)
        if bad is not None:
            raises(lambda p=pat, t=text: f(p, t), "invalid pattern %r" % (pat,))
            continue
        eq(f(pat, text), want, "random (%r, %r)" % (pat, text))

    star = "*a" * 19 + "*b"
    with time_limit(STAR_LIMIT, "20 star no-match"):
        t0 = time.perf_counter()
        got = f(star, "a" * 4000)
        dt = time.perf_counter() - t0
    eq(got, -1, "20 stars, no match")
    if dt > STAR_BUDGET:
        raise CheckFail("20 stars took %.2fs, budget is %.2fs" % (dt, STAR_BUDGET))
    with time_limit(STAR_LIMIT, "20 star match"):
        t0 = time.perf_counter()
        got = f(star, "a" * 4000 + "b")
        dt2 = time.perf_counter() - t0
    eq(got, 4001, "20 stars, match at the end")
    if dt2 > STAR_BUDGET:
        raise CheckFail("20 stars matching took %.2fs, budget is %.2fs" % (dt2, STAR_BUDGET))
    gate_record("c5_20_stars", min(dt, dt2))
    return "fixed + 250 brute-checked + 20 stars %s" % gate_label("c5_20_stars", min(dt, dt2))


def _gen_pattern(rng):
    out = []
    for _ in range(rng.randint(0, 6)):
        r = rng.random()
        if r < 0.35:
            out.append(rng.choice("abc"))
        elif r < 0.5:
            out.append("?")
        elif r < 0.65:
            out.append("*")
        elif r < 0.72:
            out.append(rng.choice(["\\*", "\\?", "\\{", "\\}", "\\,", "\\\\", "\\a"]))
        elif r < 0.85:
            branches = []
            for _ in range(rng.randint(1, 3)):
                branches.append("".join(rng.choice(["a", "b", "c", "?", "*"])
                                        for _ in range(rng.randint(0, 2))))
            out.append("{" + ",".join(branches) + "}")
        elif r < 0.92:
            out.append("{")
        else:
            out.append("}")
    return "".join(out)


# ---------------------------------------------------------------- driver

# The star gate: STAR_LIMIT is the alarm (how long a hanging candidate may run)
# and STAR_BUDGET the time a finished call may report. _apply_calibration() has
# already set both from the calibration file (STAR_LIMIT as an alarm above the
# budget), and they stay module globals so a caller can shrink them.

CHECKS_RAW = {
    "c1_csv_line": c1,
    "c2_eval_expr": c2,
    "c3_tokenize": c3,
    "c4_schedule": c4,
    "c5_shortest_match": c5,
}

# Whole-task ceiling, in seconds. A candidate that hangs anywhere -- even on a
# small case, before reaching a performance gate -- is stopped by this.
TASK_LIMIT = 300.0


def _guarded(fn):
    def inner(mod):
        with time_limit(TASK_LIMIT, "task"):
            return fn(mod)
    return inner


CHECKS = {name: _guarded(fn) for name, fn in CHECKS_RAW.items()}


GATED_TASKS = ["c3_tokenize", "c4_schedule", "c5_shortest_match"]


def calibrate(attempts=3):
    """Time the bundled reference solutions and derive the gate budgets.

    Best of `attempts` per gate, so scheduler noise does not set the budget.
    Prints JSON; the runner writes it to calibration.json and points
    BENCH_CALIBRATION at it for the graded run.
    """
    import platform
    gates = {}
    for task in GATED_TASKS:
        ref = os.path.join(HERE, "_refs", task + ".py")
        samples = {}
        for _ in range(attempts):
            GATE_TIMES.clear()
            try:
                mod = load(ref)
                CHECKS_RAW[task](mod)
            except BaseException:
                pass
            for label, dt in GATE_TIMES.items():
                samples.setdefault(label, []).append(dt)
        for label in sorted(samples):
            best = min(samples[label])
            budget = max(best * GATE_MULTIPLES[label], GATE_FLOOR[label])
            gates[label] = {
                "task": task,
                "ref_seconds": round(best, 4),
                "samples": [round(t, 4) for t in samples[label]],
                "multiple": GATE_MULTIPLES[label],
                "floor_seconds": GATE_FLOOR[label],
                "budget_seconds": round(budget, 3),
                "bound_by": "floor" if budget == GATE_FLOOR[label] else "reference",
            }
    return {
        "gates": gates,
        "attempts": attempts,
        "host": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("--list", "-l"):
        print("\n".join(sorted(CHECKS)))
        return
    if len(sys.argv) == 2 and sys.argv[1] == "--calibrate":
        print(json.dumps(calibrate(), indent=2, sort_keys=True))
        return
    task, path = sys.argv[1], sys.argv[2]
    if task not in CHECKS:
        print(json.dumps({"ok": False, "detail": "unknown task %r" % task}))
        return
    try:
        mod = load(path)
    except BaseException as e:
        print(json.dumps({"ok": False, "detail": "import failed: %s: %s" % (type(e).__name__, e)}))
        return
    try:
        note = CHECKS[task](mod)
        print(json.dumps({"ok": True, "detail": note or "all checks passed"}))
    except CheckFail as e:
        print(json.dumps({"ok": False, "detail": str(e)}))
    except Timeout:
        print(json.dumps({"ok": False, "detail": "timed out"}))
    except BaseException as e:
        print(json.dumps({"ok": False, "detail": "%s: %s" % (type(e).__name__, e)}))


if __name__ == "__main__":
    main()
