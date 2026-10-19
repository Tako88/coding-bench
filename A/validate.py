"""Validation for benchmark C. Not part of grading; run it whenever a task,
reference or checker changes.

  python3 validate.py

Phase 1: every reference solution must pass its checker.
Phase 2: deliberately wrong solutions must fail, with the expected reason --
         this is what proves the checker discriminates rather than passing
         anything.
Phase 3: the grader's own references are cross-checked against independent
         oracles (Python's csv and eval, shlex, and exhaustive brute force).
Phase 4: the checker's time limit must stop a hanging solution.
"""

import importlib.util
import io
import os
import random
import shlex
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checks  # noqa: E402
import _oracle as oracle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = ["c1_csv_line", "c2_eval_expr", "c3_tokenize", "c4_schedule", "c5_shortest_match"]

full = {"c1_csv_line": "parse_csv_line", "c2_eval_expr": "evaluate",
        "c3_tokenize": "tokenize", "c4_schedule": "best_schedule",
        "c5_shortest_match": "shortest_prefix_match"}

ok_count = 0
bad_count = 0


def report(name, ok, detail=""):
    global ok_count, bad_count
    if ok:
        ok_count += 1
        print("  PASS  %-42s %s" % (name, detail))
    else:
        bad_count += 1
        print("  FAIL  %-42s %s" % (name, detail))


def load_ref(task):
    path = os.path.join(HERE, "_refs", task + ".py")
    spec = importlib.util.spec_from_file_location("ref_" + task, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ phase 1

def phase1():
    print("phase 1: reference solutions must pass")
    for task in TASKS:
        mod = load_ref(task)
        try:
            note = checks.CHECKS[task](mod)
            report(task, True, note)
        except checks.CheckFail as e:
            report(task, False, str(e))
        except BaseException as e:
            report(task, False, "%s: %s" % (type(e).__name__, e))


# ------------------------------------------------------------------ phase 2

def naive_csv(line):
    out, cur, q, i = [], [], False, 0
    while i < len(line):
        c = line[i]
        if q:
            if c == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    cur.append('"')
                    i += 2
                    continue
                q = False
                i += 1
                continue
            cur.append(c)
            i += 1
        else:
            if c == '"':
                q = True
                i += 1
                continue
            if c == ",":
                out.append("".join(cur))
                cur = []
                i += 1
                continue
            cur.append(c)
            i += 1
    out.append("".join(cur))
    return out


def wrong_pow_left(expr):
    import _refs.c2_eval_expr as r  # noqa
    saved = r.INFIX["^"]
    r.INFIX["^"] = (6, 7)
    try:
        return r.evaluate(expr)
    finally:
        r.INFIX["^"] = saved


def wrong_unary_tight(expr):
    import _refs.c2_eval_expr as r  # noqa
    saved = r.UNARY_BP
    r.UNARY_BP = 7
    try:
        return r.evaluate(expr)
    finally:
        r.UNARY_BP = saved


def wrong_comment_anywhere(line):
    toks = line.split()
    out = []
    for t in toks:
        if "#" in t and not t.startswith("\\"):
            t = t.split("#", 1)[0]
        if t:
            out.append(t)
    return out


def wrong_no_concat(line):
    parts = []
    cur = ""
    i = 0
    while i < len(line):
        c = line[i]
        if c in " \t":
            if cur:
                parts.append(cur)
                cur = ""
            i += 1
        elif c in "'\"":
            if cur:
                parts.append(cur)
                cur = ""
            j = line.find(c, i + 1)
            if j < 0:
                raise ValueError("unterminated")
            parts.append(line[i + 1:j])
            i = j + 1
        else:
            cur += c
            i += 1
    if cur:
        parts.append(cur)
    return parts


def _schedule_common(intervals, forbid_touch=False, use_count=True):
    import bisect
    ivs = [tuple(x) for x in intervals]
    n = len(ivs)
    if n == 0:
        return (0, [])
    order = sorted(range(n), key=lambda i: (ivs[i][0], ivs[i][1], i))
    starts = [ivs[i][0] for i in order]
    P = [0] * (n + 1)
    C = [0] * (n + 1)
    pad = 1 if forbid_touch else 0
    for k in range(n - 1, -1, -1):
        s, e, p = ivs[order[k]]
        j = bisect.bisect_left(starts, e + pad, k + 1)
        cp, cc = p + P[j], 1 + C[j]
        if not use_count:
            P[k], C[k] = (cp, 0) if cp > P[k + 1] else (P[k + 1], 0)
        elif cp > P[k + 1] or (cp == P[k + 1] and cc < C[k + 1]):
            P[k], C[k] = cp, cc
        else:
            P[k], C[k] = P[k + 1], C[k + 1]

    def after(e):
        j = bisect.bisect_left(starts, e + pad)
        return (P[j], C[j])

    scan = sorted(range(n), key=lambda i: (ivs[i][0], ivs[i][1], ivs[i][2], i))
    chosen = []
    t = 0
    rp, rc = P[0], C[0]
    for i in scan:
        if rp == 0:
            break
        s, e, p = ivs[i]
        if s < t:
            continue
        hp, hc = after(e)
        if p + hp == rp and (not use_count or 1 + hc == rc):
            chosen.append((s, e, p))
            t = e
            rp -= p
            rc -= 1
    return (P[0], chosen)


def wrong_schedule_no_count(intervals):
    return _schedule_common(intervals, use_count=False)


def wrong_schedule_no_touch(intervals):
    return _schedule_common(intervals, forbid_touch=True)


def wrong_match_whole_text(pattern, text):
    elems = oracle.parse_elements(pattern)
    ps = oracle.brute_positions(elems, text, 0)
    return len(text) if len(text) in ps else -1


def wrong_match_backtracking(pattern, text):
    """Correct but exponential: the shape a model reaches for by default.
    Handles groups too, so it reaches the performance gate instead of failing
    earlier on a group case."""
    elems = oracle.parse_elements(pattern)
    for L in range(len(text) + 1):
        if _naive_match(elems, 0, text, 0, L):
            return L
    return -1


def _naive_match(elems, ei, text, ti, limit):
    if ei == len(elems):
        return ti == limit
    e = elems[ei]
    k = e[0]
    if k == "c":
        return ti < limit and text[ti] == e[1] and _naive_match(elems, ei + 1, text, ti + 1, limit)
    if k == "q":
        return ti < limit and _naive_match(elems, ei + 1, text, ti + 1, limit)
    if k == "s":
        for nxt in range(ti, limit + 1):
            if _naive_match(elems, ei + 1, text, nxt, limit):
                return True
        return False
    for branch in e[1]:
        for end in oracle.brute_positions(branch, text, ti):
            if _naive_match(elems, ei + 1, text, end, limit):
                return True
    return False


def phase2():
    print("phase 2: wrong solutions must fail")
    cases = [
        ("c1 naive quote-mid-field", "c1_csv_line", SimpleNamespace(parse_csv_line=naive_csv)),
        ("c2 '^' as left associative", "c2_eval_expr", SimpleNamespace(evaluate=wrong_pow_left)),
        ("c2 unary tighter than '^'", "c2_eval_expr", SimpleNamespace(evaluate=wrong_unary_tight)),
        ("c3 '#' comments anywhere", "c3_tokenize", SimpleNamespace(tokenize=wrong_comment_anywhere)),
        ("c3 no segment concatenation", "c3_tokenize", SimpleNamespace(tokenize=wrong_no_concat)),
        ("c4 ignores minimum count", "c4_schedule", SimpleNamespace(best_schedule=wrong_schedule_no_count)),
        ("c4 touching forbidden", "c4_schedule", SimpleNamespace(best_schedule=wrong_schedule_no_touch)),
        ("c5 ignores shortest prefix", "c5_shortest_match", SimpleNamespace(shortest_prefix_match=wrong_match_whole_text)),
    ]
    for name, task, mod in cases:
        try:
            note = checks.CHECKS[task](mod)
            report(name, False, "checker accepted it (%s)" % note)
        except checks.CheckFail as e:
            report(name, True, "rejected: %s" % str(e)[:70])
        except BaseException as e:
            report(name, True, "rejected: %s: %s" % (type(e).__name__, str(e)[:60]))

    # the star gate on its own: this matcher is correct for every small case and
    # only the performance gate can reject it. Shrink the gate so the check is
    # fast; a real run uses checks.STAR_LIMIT.
    saved = checks.STAR_LIMIT
    checks.STAR_LIMIT = 6.0
    try:
        note = checks.CHECKS["c5_shortest_match"](
            SimpleNamespace(shortest_prefix_match=wrong_match_backtracking))
        report("c5 exponential matcher rejected by the star gate", False,
               "checker accepted it (%s)" % note)
    except checks.CheckFail as e:
        report("c5 exponential matcher rejected by the star gate", "star" in str(e),
               str(e)[:75])
    except BaseException as e:
        report("c5 exponential matcher rejected by the star gate", False,
               "%s: %s" % (type(e).__name__, str(e)[:60]))
    finally:
        checks.STAR_LIMIT = saved


# ------------------------------------------------------------------ phase 3

def phase3():
    print("phase 3: references against independent oracles")
    import csv as csvmod
    import re
    rng = random.Random(1234)

    # c1 vs the stdlib csv module: generate fields, render, compare both parsers
    disagree = 0
    for _ in range(2000):
        fields = ["".join(rng.choice("ab,\" x") for _ in range(rng.randint(0, 5)))
                  for _ in range(rng.randint(1, 4))]
        parts = []
        for s in fields:
            if s == "" or "," in s or '"' in s:
                parts.append('"' + s.replace('"', '""') + '"')
            else:
                parts.append(s)
        line = ",".join(parts)
        try:
            std = next(csvmod.reader(io.StringIO(line), strict=True))
        except Exception:
            std = None
        ref = oracle.ref_csv(line)
        if std is not None and std != ref:
            disagree += 1
            if disagree < 4:
                print("        csv disagreement: %r -> std %r ref %r" % (line, std, ref))
    report("c1 ref vs stdlib csv (2000 records)", disagree == 0, "%d disagreements" % disagree)

    # c2 vs Python eval: '^' -> '**' is faithful (right assoc, tighter than unary)
    disagree = 0
    for _ in range(3000):
        src = checks._gen_expr(rng)
        try:
            want = float(eval(src.replace("^", "**"), {"__builtins__": {}}, {}))
            werr = None
        except BaseException as e:
            want, werr = None, type(e)
        try:
            got = oracle.ref_evaluate(src)
            gerr = None
        except BaseException as e:
            got, gerr = None, type(e)
        if werr is not None or gerr is not None:
            if werr is not gerr:
                disagree += 1
            continue
        if abs(float(got) - float(want)) > 1e-9 * max(1.0, abs(float(want))):
            disagree += 1
            if disagree < 4:
                print("        eval disagreement: %r -> python %r ref %r" % (src, want, got))
    report("c2 ref vs python eval (3000 expressions)", disagree == 0, "%d disagreements" % disagree)

    # c3 vs shlex: the pool has no '#', because shlex starts a comment anywhere
    # while the task spec only starts one at the beginning of a token. That one
    # intentional difference is pinned separately below.
    pool = "ab xyz,;'\"\\-+=\t"
    mismatch = 0
    checked = 0
    for _ in range(3000):
        line = "".join(rng.choice(pool) for _ in range(rng.randint(0, 10)))
        try:
            want = shlex.split(line, comments=False, posix=True)
            werr = None
        except ValueError as e:
            want, werr = None, str(e)
        try:
            got = oracle.ref_tokenize(line)
            gerr = None
        except ValueError as e:
            got, gerr = None, str(e)
        checked += 1
        if (werr is None) != (gerr is None) or (werr is None and want != got):
            mismatch += 1
            if mismatch < 6:
                print("        shlex disagreement: %r -> shlex %r (%s) ref %r (%s)"
                      % (line, want, werr, got, gerr))
    report("c3 ref vs shlex (%d lines, no #)" % checked, mismatch == 0,
           "%d disagreements" % mismatch)

    # comment rule: shlex with comments=True agrees everywhere except a '#' that
    # follows a non-space inside a token, where the spec keeps it literal.
    comment_cases = ["a #b", "#a", "zx   #b", "a '#b'", 'a"#b"', "a\\#b", "\\#a",
                     "#", "ab\t#comment here", "  #"]
    bad = []
    for line in comment_cases:
        want = shlex.split(line, comments=True, posix=True)
        got = oracle.ref_tokenize(line)
        if want != got:
            bad.append((line, want, got))
    report("c3 comment rule vs shlex comments=True", not bad, str(bad[:3]))
    mid = oracle.ref_tokenize("a#b")
    other = shlex.split("a#b", comments=True, posix=True)
    report("c3 mid-token '#' stays literal (documents divergence)",
           mid == ["a#b"] and other == ["a"], "ref %r shlex %r" % (mid, other))

    # c4 ref vs exhaustive brute force
    mism = 0
    for _ in range(600):
        ivs = []
        for _ in range(rng.randint(0, 10)):
            s = rng.randint(0, 7)
            ivs.append((s, s + rng.randint(1, 4), rng.randint(1, 5)))
        if oracle.ref_schedule(ivs) != oracle.brute_schedule(ivs):
            mism += 1
            if mism < 4:
                print("        brute disagreement: %r -> ref %r brute %r"
                      % (ivs, oracle.ref_schedule(ivs), oracle.brute_schedule(ivs)))
    report("c4 ref vs exhaustive subsets (600 cases)", mism == 0, "%d disagreements" % mism)

    # c5 ref vs brute force
    mism = 0
    tried = 0
    for _ in range(1500):
        pat = checks._gen_pattern(rng)
        txt = "".join(rng.choice("abc") for _ in range(rng.randint(0, 10)))
        try:
            want = oracle.brute_shortest(pat, txt)
            werr = None
        except ValueError as e:
            want, werr = None, str(e)
        try:
            got = oracle.ref_shortest(pat, txt)
            gerr = None
        except ValueError as e:
            got, gerr = None, str(e)
        tried += 1
        if (werr is None) != (gerr is None) or (werr is None and want != got):
            mism += 1
            if mism < 6:
                print("        brute disagreement: (%r,%r) -> brute %r (%s) nfa %r (%s)"
                      % (pat, txt, want, werr, got, gerr))
    report("c5 ref vs exhaustive match (%d cases)" % tried, mism == 0, "%d disagreements" % mism)


# ------------------------------------------------------------------ phase 4

def phase4():
    print("phase 4: a hanging solution must be stopped")

    def spin(*a, **k):
        while True:
            pass

    saved = checks.TASK_LIMIT
    checks.TASK_LIMIT = 8.0
    mod = SimpleNamespace(tokenize=spin)
    t0 = time.time()
    try:
        checks.CHECKS["c3_tokenize"](mod)
        report("hanging solution stopped", False, "checker returned normally")
    except checks.CheckFail as e:
        report("hanging solution stopped", "finish within" in str(e),
               "%s (%.1fs)" % (str(e)[:70], time.time() - t0))
    except BaseException as e:
        report("hanging solution stopped", False, "%s: %s" % (type(e).__name__, e))
    finally:
        checks.TASK_LIMIT = saved


if __name__ == "__main__":
    t0 = time.time()
    for fn in (phase1, phase2, phase3, phase4):
        fn()
    print("\n%d checks passed, %d failed (%.1fs)" % (ok_count, bad_count, time.time() - t0))
    sys.exit(1 if bad_count else 0)
