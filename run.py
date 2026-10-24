#!/usr/bin/env python3
"""Runner and evidence collector for the agentic coding benchmark.

    python3 run.py runs                     list the runs in benchmark A
    python3 run.py check [route ...]        one cheap turn per route: go/no-go
    python3 run.py run --name baseline      walk the queue as a named run (--detach to background it)
    python3 run.py status [--name x]        per-run progress
    python3 run.py table [--name x]         results table(s) from the evidence
    python3 run.py watch                    live transcript of whatever is running
    python3 run.py stats <cell-dir>         one cell's parsed stats

A benchmark (A/, B/) is the sealed instrument: tasks, prompts, graders, gates.
A run is one named experiment inside it: <bench>/runs/<name>/<route>/<task>/, so
you can run the queue, change the sampler, and start a second run without the two
overwriting or silently skipping each other's cells. Add --bench to address a
benchmark other than A.

What the model sees is sealed inside the benchmark directory. What the runner did
is recorded in each cell's meta.json -- commands, sampling, versions, calibration,
timings, tokens, grade -- so a result can be re-checked without trusting this
script. Every number in run.log and RESULTS-<run>.md is parsed from a transcript or
a measurement; none is typed by hand.

Requirements: python3 (stdlib only), pi on PATH, a reachable model endpoint.
"""

import argparse
import collections
import hashlib
import json
import os
import re
import resource
import shutil
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = "A"                # which benchmark: A/, B/ ... each is a sealed instrument (tasks, prompts, graders)
RUN = None                 # which named run inside that benchmark: <bench>/runs/<name>/
DEFAULT_RUN = "baseline"   # the name `run` uses when --name is omitted
TASKS = ["c1_csv_line", "c2_eval_expr", "c3_tokenize", "c4_schedule", "c5_shortest_match"]

DEFAULT_CAP = 1800          # seconds per cell; the spec's own figure
GRADE_TIMEOUT = 400         # checks.py's TASK_LIMIT is 300s
GRADE_MEM_KB = 3_000_000    # address-space cap for grading a candidate solution
CELL_MEM_MB = 4096          # physical memory cap for the whole cell (pi + the model's own tools),
                            # enforced by a systemd user scope, not by RLIMIT_AS: an address-space
                            # cap breaks Node (undici's WASM llhttp cannot instantiate under it)
PROBE_CAP = 90           # --check: the first turn is enough


# ------------------------------------------------------------------ small helpers

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def read(path):
    with open(path, errors="replace") as fh:
        return fh.read()


def bench_dir():
    return os.path.join(HERE, BENCH)


def list_runs():
    """Runs that already have evidence.

    A directory counts as a run only if it holds a queued.json, which the runner
    writes when a run starts. That keeps leftover directories from earlier
    layouts out of the listing. '_'-prefixed names are scratch.
    """
    root = os.path.join(bench_dir(), "runs")
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root)
                  if not d.startswith("_")
                  and os.path.exists(os.path.join(root, d, "queued.json")))


def run_root(name=None):
    """Directory of one named run inside the benchmark."""
    name = name or RUN
    if not name:
        sys.exit("this needs a run name: --name <run>   (existing: %s)"
                 % (", ".join(list_runs()) or "none"))
    return os.path.join(bench_dir(), "runs", name)


def route_dir(run_name, route_name):
    return os.path.join(run_root(run_name), route_name)


def list_benchmarks():
    return sorted(d for d in os.listdir(HERE)
                  if os.path.isdir(os.path.join(HERE, d)) and os.path.exists(os.path.join(HERE, d, "MANIFEST.json")))


def load_queue():
    """models.txt: 'route [cap]' per line, '#' comments. Returns [(route, cap)]."""
    path = os.path.join(HERE, "models.txt")
    queue = []
    if not os.path.exists(path):
        sys.exit("no models.txt in %s" % HERE)
    for line in read(path).splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        route = parts[0]
        cap = int(parts[1]) if len(parts) > 1 else None
        queue.append((route, cap))
    return queue


def load_route(name):
    path = os.path.join(HERE, "routes", name + ".json")
    if not os.path.exists(path):
        sys.exit("no route file: %s" % path)
    return json.loads(read(path))


def route_weights(route):
    """The structured weights block: which model file this route runs.

    Named "weights", not "model", because an endpoint route already uses "model"
    for the endpoint's own model entry (id, contextWindow, maxTokens).
    """
    return route.get("weights") or {}


def route_label(route):
    """Display name, composed from the model block.

    One resolver for the score table, the sampler table and the run header. When
    the name was free text, a route could appear under two different names in the
    same results file: the score table took it from a cell's meta.json (so an
    unrun route showed its bare route name) while the sampler table took it from
    the plan. Composing it from the model block makes both the same by
    construction, and a new route cannot be quieter than the others.
    """
    m = route_weights(route)
    if not m:
        return route.get("label") or route.get("pi_model") or \
            (route.get("model") or {}).get("id") or "?"
    name = m.get("name") or route.get("label") or "?"
    if m.get("quant"):
        name += " " + m["quant"]          # every row states its quant, exactly once
    d = m.get("drafter") or {}
    if d.get("kind"):
        name += " + %s" % d["kind"]
    tail = [b for b in (m.get("stack"), ("%s ctx" % m["ctx"]) if m.get("ctx") else None) if b]
    return "%s (%s)" % (name, ", ".join(tail)) if tail else name


def entry_label(entry):
    """Canonical name for a queued entry; falls back to the plan if the file is gone."""
    try:
        return route_label(load_route(entry["route"]))
    except SystemExit:
        return entry.get("label") or entry["route"]


def selected(names):
    queue = load_queue()
    if not names:
        return queue
    known = {r for r, _ in queue}
    for n in names:
        if n not in known:
            sys.exit("route %r is not in models.txt (%s)" % (n, ", ".join(sorted(known))))
    return [(r, c) for r, c in queue if r in names]


# ------------------------------------------------------------------ transcripts

def newest_session(cell):
    d = os.path.join(cell, "sessions")
    if not os.path.isdir(d):
        return None
    files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".jsonl")]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def stats(path):
    """Parse a pi session file: turns, tokens, tool calls, compactions, repeats."""
    turns = out = reasoning = comp = reps = duration_ms = 0
    calls = collections.Counter()
    last = ""
    if path and os.path.exists(path):
        for line in read(path).splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("type") == "compaction":
                comp += 1
                continue
            if rec.get("type") != "message":
                continue
            msg = rec.get("message") or {}
            if msg.get("role") != "assistant":
                continue
            turns += 1
            usage = msg.get("usage") or {}
            out += usage.get("output") or 0
            reasoning += usage.get("reasoning") or 0
            duration_ms += msg.get("durationMs") or 0
            parts = []
            for block in (msg.get("content") or []):
                if isinstance(block, dict):
                    if block.get("type") in ("toolCall", "tool_use"):
                        calls[block.get("name")] += 1
                    parts.append(str(block.get("text") or block.get("thinking") or ""))
            text = " ".join(parts)
            if text:
                last = text[:160]
            windows = collections.Counter(text[i:i + 60] for i in range(0, max(1, len(text) - 60), 30))
            if windows and windows.most_common(1)[0][1] > 1:
                reps += 1
    return {"turns": turns, "out": out, "reasoning": reasoning, "calls": dict(calls),
            "comp": comp, "rep_turns": reps, "duration_ms": duration_ms, "last": last}


def partial_chars(path):
    """Characters streamed since the last completed turn.

    A pi session file only contains completed messages, so a cell killed
    mid-message loses that message's usage. The event stream still holds the
    deltas, so count them: a nonzero figure means the token totals below are a
    floor, not the whole story.
    """
    tail_chars = 0
    if path and os.path.exists(path):
        for line in read(path).splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            kind = rec.get("type")
            if kind in ("turn_end", "agent_end", "agent_settled"):
                tail_chars = 0
                continue
            if kind != "message_update":
                continue
            ev = rec.get("assistantMessageEvent") or {}
            if str(ev.get("type") or "").endswith("_delta"):
                tail_chars += len(ev.get("delta") or "")
    return tail_chars


def finish_status(st):
    """DONE / BLOCKED / unfinished, read from the model's own last words."""
    tail = (st.get("last") or "").upper()
    if re.search(r"\bBLOCKED\b", tail):
        return "BLOCKED"
    if re.search(r"\bDONE\b", tail):
        return "DONE"
    return "unfinished"


# ------------------------------------------------------------------ route config

def sampling_source(info):
    """Where the sampler comes from: our request, or the engine's own defaults.

    A route whose model entry carries no samplingParams sends none, so the values in
    force are whatever the server decides (llama.cpp's built-ins, or the GGUF's
    embedded metadata, or the launch flags). Recording which of the two happened
    keeps a dash in the results table from reading as missing data.
    """
    if (info.get("sampling") or {}).get("samplingParams"):
        return "request"
    return "engine default"


def resolve_route(route, run_dir):
    """Where this route actually points: pi model pattern, base URL, config dir.

    An endpoint route gets a scratch config dir. A pi_model route reuses the
    user's own models.json, so the runner reads that file to record which base
    URL and sampling the run really used.
    """
    if route.get("pi_model"):
        pattern = route["pi_model"]
        provider = pattern.split("/", 1)[0]
        cfg_dir = os.environ.get("PI_CODING_AGENT_DIR") or os.path.expanduser("~/.pi/agent")
        info = {"model_pattern": pattern, "provider": provider, "config_dir": cfg_dir,
                "base_url": None, "model_id": pattern.split("/", 1)[-1], "sampling": None,
                "api_key": None}
        path = os.path.join(cfg_dir, "models.json")
        if os.path.exists(path):
            try:
                prov = (json.loads(read(path)).get("providers") or {}).get(provider) or {}
                info["base_url"] = prov.get("baseUrl")
                info["api_key"] = expand_env(prov.get("apiKey"))
                for m in prov.get("models") or []:
                    if m.get("id") == pattern.split("/", 1)[-1]:
                        info["sampling"] = {k: m[k] for k in
                                            ("samplingParams", "samplingParamsByThinkingLevel",
                                             "contextWindow", "maxTokens", "reasoning") if k in m}
            except (ValueError, OSError):
                pass
        return info
    cfg, pattern = materialize_config(run_dir, route)
    return {"model_pattern": pattern, "provider": pattern.split("/", 1)[0],
            "config_dir": cfg, "base_url": (route.get("endpoint") or {}).get("baseUrl"),
            "model_id": (route.get("model") or {}).get("id"),
            "api_key": expand_env((route.get("endpoint") or {}).get("apiKey")),
            "sampling": {"samplingParams": route.get("samplingParams"),
                         "contextWindow": (route.get("model") or {}).get("contextWindow")}}


def expand_env(value):
    """pi resolves $VAR in models.json; do the same for the runner's warm-up."""
    if not isinstance(value, str) or not value or value.startswith("!"):
        return None
    return re.sub(r"\$\{?(\w+)\}?", lambda m: os.environ.get(m.group(1), ""), value)


LOADING_MARKERS = ("llama-swap", "loading model", "model is loading", "starting server")


def warm_up(info, quiet=True):
    """Wait until the endpoint answers with real model output.

    A swap/proxy in front of the model answers the first request with a loading
    page instead of the model, and that page lands in the transcript as if the
    model had said it. One throwaway 1-token completion moves the model load (and
    that banner) out of the measured window.
    """
    base = info.get("base_url")
    if not base:
        return {"ok": None, "waited": 0, "detail": "no base URL known; skipped"}
    import urllib.error
    import urllib.request
    url = base.rstrip("/") + "/chat/completions"
    headers = {"content-type": "application/json"}
    key = info.get("api_key")
    if key:
        headers["authorization"] = "Bearer " + key
    body = json.dumps({"model": info.get("model_id") or "probe", "max_tokens": 1,
                       "messages": [{"role": "user", "content": "hi"}]}).encode()
    t0 = time.time()
    detail = ""
    refused = 0
    while time.time() - t0 < 900:
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as rsp:
                text = rsp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404):
                return {"ok": None, "waited": round(time.time() - t0, 1),
                        "detail": "warm-up got HTTP %d; continuing without it" % e.code}
            detail = "HTTP %d" % e.code
            time.sleep(2)
            continue
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            detail = "%s: %s" % (type(e).__name__, e)
            if "refused" in str(e).lower():
                refused += 1
                if refused >= 3:
                    return {"ok": False, "waited": round(time.time() - t0, 1),
                            "detail": "connection refused three times: nothing is listening on %s" % base}
            time.sleep(2)
            continue
        if any(m in text.lower() for m in LOADING_MARKERS):
            detail = "endpoint still loading"
            time.sleep(2)
            continue
        return {"ok": True, "waited": round(time.time() - t0, 1), "detail": "endpoint ready"}
    return {"ok": False, "waited": round(time.time() - t0, 1), "detail": detail or "timed out"}


def materialize_config(run_dir, route):
    """Write a scratch pi config dir for an endpoint route. None for pi_model routes."""
    if route.get("pi_model"):
        return None
    endpoint = route.get("endpoint") or {}
    model = route.get("model") or {}
    if not endpoint.get("baseUrl") or not model.get("id"):
        sys.exit("route needs either \"pi_model\" or \"endpoint.baseUrl\" + \"model.id\"")
    provider = endpoint.get("provider", "bench")
    entry = {
        "id": model["id"],
        "name": route_label(route),
        "api": endpoint.get("api", "openai-completions"),
        "contextWindow": model.get("contextWindow", 65536),
        "maxTokens": model.get("maxTokens", model.get("contextWindow", 65536)),
        "reasoning": bool(model.get("reasoning", True)),
        "input": ["text"],
    }
    for key in ("samplingParams", "samplingParamsByThinkingLevel", "thinkingLevelMap",
                "compat", "cost"):
        if route.get(key) is not None:
            entry[key] = route[key]
    if model.get("compat") is not None:
        entry["compat"] = model["compat"]
    cfg = os.path.join(run_dir, ".pi-config")
    os.makedirs(cfg, exist_ok=True)
    with open(os.path.join(cfg, "models.json"), "w") as fh:
        json.dump({"providers": {provider: {
            "name": route_label(route),
            "baseUrl": endpoint["baseUrl"],
            "api": endpoint.get("api", "openai-completions"),
            "apiKey": endpoint.get("apiKey", "local"),
            "models": [entry],
        }}}, fh, indent=2, sort_keys=True)
    return cfg, "%s/%s" % (provider, model["id"])


def pi_command(route, model_pattern, cell, system_prompt, task):
    tools = read(os.path.join(bench_dir(), "tools.txt")).strip()
    cmd = [
        "pi", "--mode", "json", "-p",
        "--model", model_pattern,
        "--tools", tools,
        "--no-context-files", "--no-skills", "--no-extensions",
        "--no-prompt-templates", "--no-mcp", "--no-themes", "--no-approve", "--offline",
        "--append-system-prompt", system_prompt,
        "--session-dir", os.path.join(cell, "sessions"),
        "--name", task,
    ]
    # --exclude-tools "*" then --tools allowlist: the allowlist is what re-enables.
    thinking = route.get("thinking")
    if thinking:
        cmd += ["--thinking", thinking]
    return cmd


# ------------------------------------------------------------------ one cell

def grade(task, solution, calibration):
    env = dict(os.environ)
    if calibration:
        env["BENCH_CALIBRATION"] = calibration
    argv = [sys.executable, os.path.join(bench_dir(), "checks.py"), task, solution]

    def cap():
        import resource
        limit = GRADE_MEM_KB * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

    try:
        proc = subprocess.run(argv, capture_output=True, text=True, env=env,
                              preexec_fn=cap, timeout=GRADE_TIMEOUT)
        out = proc.stdout.strip().splitlines()
        return json.loads(out[-1]) if out else {"ok": False, "detail": "grader produced no output"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "detail": "grading timed out after %ds" % GRADE_TIMEOUT}
    except ValueError:
        return {"ok": False, "detail": "grader output not JSON: %r" % out[-1][:200]}


CELL_PROBE = {}   # cached once: {"wrapper": [...], "mechanism": str}


def cell_wrapper():
    """Prefix that puts a cell in its own memory-capped cgroup, if this host can do it.

    A cell runs the model's own bash tools, and those tools' test scripts are what
    grow without bound: a 5 GB pattern fuzzer was observed on a box where the
    serving engine already held 22 GB, so the kernel had to step in and the model
    was left guessing why it died.

    The cap is on *physical* memory (systemd-run's MemoryMax), not virtual: RLIMIT_AS
    cannot be used here because Node reserves enough address space that undici's
    WASM llhttp fails to instantiate and pi dies at startup. The reference solutions
    pass under 256 MB, so 4 GB is generous while keeping a runaway script from
    taking the desktop with it. Grading has its own separate cap.

    Portability: `systemd-run --user --scope` is available on systemd distros and
    absent on macOS/BSD/containers. Existence is not enough -- a container can have
    the binary and no user manager to talk to -- so this probes once with a trivial
    command and falls back to running the cell uncapped, recording which happened so
    the evidence never claims a cap that was not there.
    """
    if CELL_PROBE:
        return CELL_PROBE["wrapper"]
    wrapper = ["systemd-run", "--user", "--scope", "--quiet",
               "-p", "MemoryMax=%dM" % CELL_MEM_MB, "-p", "MemorySwapMax=0", "--"]
    mechanism = "none (systemd-run not found)"
    if shutil.which("systemd-run"):
        mechanism = "none (systemd-run --user --scope failed)"
        try:
            probe = subprocess.run(wrapper + ["true"], capture_output=True, timeout=30)
            if probe.returncode == 0:
                CELL_PROBE.update(wrapper=wrapper, mechanism="systemd-run --scope MemoryMax=%dM" % CELL_MEM_MB)
                return wrapper
        except (OSError, subprocess.SubprocessError):
            pass
    CELL_PROBE.update(wrapper=[], mechanism=mechanism)
    return []


def terminate_cell(proc, grace=5):      # pi ignores SIGTERM and rides out SIGINT briefly
                                          # before this SIGKILL lands, so keep it short
    """Stop one cell's process group: SIGINT first, SIGKILL if it will not go.

    A cell runs in its own session, so the whole group has to be signalled --
    otherwise a model call or a test it spawned outlives the runner.
    """
    if proc.poll() is not None:
        return proc.returncode
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except OSError:
        return proc.returncode
    try:
        return proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            pass
        return proc.wait()


CELL_PROC = {"proc": None}      # the cell currently running, for the signal handler


def run_cell(route_name, route, info, run_dir, task, cap, calibration, dry):
    cell = os.path.join(run_dir, task)
    meta_path = os.path.join(cell, "meta.json")
    if os.path.exists(meta_path) and not os.environ.get("FORCE"):
        return "skipped"
    round_d = bench_dir()
    system_prompt = read(os.path.join(round_d, "prompts", "system.txt")).strip()
    task_prompt = read(os.path.join(round_d, "prompts", "task.txt"))
    model_pattern = info["model_pattern"]
    if not dry:
        os.makedirs(cell, exist_ok=True)
        shutil.copyfile(os.path.join(round_d, "tasks", task + ".md"), os.path.join(cell, "TASK.md"))
    task_prompt = task_prompt.replace("{DIR}", cell)

    env = dict(os.environ)
    env.update({"PI_OFFLINE": "1", "PI_SKIP_VERSION_CHECK": "1", "PI_TELEMETRY": "0"})
    if route.get("env"):
        env.update({k: str(v) for k, v in route["env"].items()})
    cmd = pi_command(route, model_pattern, cell, system_prompt, task)
    if info.get("config_dir") and not route.get("pi_model"):
        env["PI_CODING_AGENT_DIR"] = info["config_dir"]

    if dry:
        print("  cd %s && %s -- %s" % (cell, " ".join(cmd), "<prompts/task.txt>"))
        return "dry"

    ready = warm_up(info)
    print("   warm-up : %s" % json.dumps(ready), flush=True)
    t0 = time.time()
    timed_out = False
    with open(os.path.join(cell, "pi.jsonl"), "w") as out, open(os.path.join(cell, "pi.err"), "w") as err:
        proc = subprocess.Popen(cell_wrapper() + cmd + ["--", task_prompt], cwd=cell, env=env,
                                stdout=out, stderr=err, start_new_session=True)
        CELL_PROC["proc"] = proc          # so a killed runner takes its cell with it
        try:
            rc = proc.wait(timeout=cap)
        except subprocess.TimeoutExpired:
            timed_out = True
            rc = terminate_cell(proc)
        finally:
            CELL_PROC["proc"] = None
    wall = int(round(time.time() - t0))

    st = stats(newest_session(cell))
    st["partial_chars"] = partial_chars(os.path.join(cell, "pi.jsonl"))
    st["source"] = "session (completed messages; partial_chars is the unfinished tail)"
    solution = os.path.join(cell, "solution.py")
    if os.path.exists(solution):
        g = grade(task, solution, calibration)
    else:
        g = {"ok": False, "detail": "no solution.py produced"}
    note = finish_status(st)
    if timed_out:
        note = "cap" if note == "unfinished" else note + "+cap"

    meta = {
        "bench": BENCH, "run": RUN, "route": route_name, "label": route_label(route),
        "weights": route_weights(route),
        "task": task, "model_pattern": info["model_pattern"], "route_file": route_name + ".json",
        "base_url": info.get("base_url"),
        "route_sampling": info.get("sampling"),
        "route_sampling_source": sampling_source(info),
        "warm_up": ready,
        "round_manifest": manifest_hash(), "runner_sha256": sha256(os.path.abspath(__file__)),
        "pi_version": pi_version(), "python": sys.version.split()[0], "host": os.uname().nodename,
        "cap_seconds": cap, "wall_seconds": wall, "killed_at_cap": timed_out,
        "cell_mem_cap_mb": CELL_MEM_MB,
        "cell_mem_mechanism": CELL_PROBE.get("mechanism", "not probed"),
        "finished": note, "grade": g, "stats": st,
        "transcript": os.path.basename(newest_session(cell) or ""),
        "solution_sha256": sha256(solution) if os.path.exists(solution) else None,
        "calibration": os.path.basename(calibration) if calibration else None,
        "sampling": route.get("samplingParams"), "thinking": route.get("thinking"),
        "endpoint": (route.get("endpoint") or {}).get("baseUrl"),
        "pi_model": route.get("pi_model"),
        "when": now(),
    }
    with open(meta_path, "w") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)
    log_line = format_line(meta)
    # one run.log per run, next to its queued.json/calibration.json (run_dir is the route dir)
    with open(os.path.join(os.path.dirname(run_dir), "run.log"), "a") as fh:
        fh.write(log_line + "\n")
    print("  " + log_line, flush=True)
    return "ran"


def format_line(m):
    st = m["stats"]
    calls = json.dumps(st["calls"], sort_keys=True, separators=(",", ":"))
    verdict = "PASS" if m["grade"].get("ok") else "FAIL"
    tail = " partial=%dc" % st["partial_chars"] if st.get("partial_chars") else ""
    return ("%-18s %5ss %-11s %-4s out=%d reasoning=%d turns=%d calls=%s comp=%d rep_turns=%d%s  %s"
            % (m["task"], m["wall_seconds"], m["finished"], verdict, st["out"], st["reasoning"],
               st["turns"], calls, st["comp"], st["rep_turns"], tail, json.dumps(m["grade"])))

def pi_version():
    try:
        p = subprocess.run(["pi", "--version"], capture_output=True, text=True, timeout=30)
        return (p.stdout or p.stderr).strip().splitlines()[0]
    except Exception:
        return "unknown"


def manifest_hash():
    path = os.path.join(bench_dir(), "MANIFEST.json")
    return sha256(path) if os.path.exists(path) else None


def calibrate(run_dir, force=False):
    """Per-run calibration of the perf gates; recorded with the evidence."""
    dest = os.path.join(run_dir, "calibration.json")
    if os.path.exists(dest) and not force:
        return dest
    out = subprocess.run([sys.executable, os.path.join(bench_dir(), "checks.py"), "--calibrate"],
                         capture_output=True, text=True, timeout=900).stdout
    calib = json.loads(out)
    calib["pi_version"] = pi_version()
    calib["round_manifest"] = manifest_hash()
    with open(dest, "w") as fh:
        json.dump(calib, fh, indent=2, sort_keys=True)
    return dest


# ------------------------------------------------------------------ subcommands

def fmt_sampling(info):
    """One line describing the sampler the route will actually send."""
    s = (info.get("sampling") or {}).get("samplingParams") or {}
    if not s:
        return "sampling: engine/server defaults (no samplingParams on this entry)"
    label = {"temperature": "temperature", "top_p": "top_p", "top_k": "top_k", "min_p": "min_p",
             "presence_penalty": "presence", "repeat_penalty": "repeat",
             "repetition_penalty": "repeat", "frequency_penalty": "frequency"}
    order = ["temperature", "top_p", "top_k", "min_p", "presence_penalty", "repeat_penalty"]
    parts = ["%s=%s" % (label[k], s[k]) for k in order if k in s]
    parts += ["%s=%s" % (label.get(k, k), s[k]) for k in sorted(s) if k not in order]
    return "sampling " + " ".join(parts)


def cmd_check(args):
    system_prompt = read(os.path.join(bench_dir(), "prompts", "system.txt")).strip()
    task_prompt = read(os.path.join(bench_dir(), "prompts", "task.txt"))
    print("%-22s %-6s %s" % ("route", "status", "detail"))
    for route_name, cap in selected(args.routes):
        route = load_route(route_name)
        probe = os.path.join(HERE, ".probe", route_name)
        os.makedirs(probe, exist_ok=True)
        shutil.copyfile(os.path.join(bench_dir(), "tasks", TASKS[0] + ".md"),
                        os.path.join(probe, "TASK.md"))
        env = dict(os.environ)
        env.update({"PI_OFFLINE": "1", "PI_SKIP_VERSION_CHECK": "1", "PI_TELEMETRY": "0"})
        if route.get("env"):
            env.update({k: str(v) for k, v in route["env"].items()})
        info = resolve_route(route, probe)
        if info.get("config_dir") and not route.get("pi_model"):
            env["PI_CODING_AGENT_DIR"] = info["config_dir"]
        ready = warm_up(info)
        cmd = pi_command(route, info["model_pattern"], probe, system_prompt, TASKS[0])
        t0 = time.time()
        try:
            proc = subprocess.run(cell_wrapper() + cmd + ["--", task_prompt.replace("{DIR}", probe)],
                                  cwd=probe, env=env, capture_output=True, text=True,
                                  timeout=PROBE_CAP)
            rc = proc.returncode
            with open(os.path.join(probe, "pi.jsonl"), "w") as fh:
                fh.write(proc.stdout or "")
        except subprocess.TimeoutExpired as e:
            rc = -1
            with open(os.path.join(probe, "pi.jsonl"), "w") as fh:
                fh.write((e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes)
                         else (e.stdout or ""))
        wall = time.time() - t0
        st = stats(newest_session(probe))
        calls = st["calls"]
        model_secs = (st["duration_ms"] or 0) / 1000.0
        speed = "%.1f t/s model-side" % (st["out"] / model_secs) if model_secs > 0 else "no timing"
        if not ready.get("ok") and ready.get("ok") is not None:
            print("%-22s %-6s %s" % (route_name, "FAIL",
                                     "endpoint never became ready: %s" % ready.get("detail")))
        elif calls:
            print("%-22s %-6s %s" % (route_name, "ok",
                                     "tool call(s) %s, %d turns, %d out tok (%d reasoning, %s), "
                                     "warm-up %ss, cell %.0fs\n%-22s %s" %
                                     (json.dumps(calls, sort_keys=True), st["turns"], st["out"],
                                      st["reasoning"], speed, ready.get("waited"), wall,
                                      "", fmt_sampling(info))))
        else:
            print("%-22s %-6s %s" % (route_name, "FAIL",
                                     "no tool call in the first turn (rc=%s, %d out tok) - "
                                     "this model does not act, or the route is wrong" % (rc, st["out"])))
    if args.name:
        for route_name, _cap in selected(args.routes):
            rec = recorded_config(route_dir(args.name, route_name)) or {}
            try:
                current = route_label(load_route(route_name))
            except SystemExit:
                continue            # route file deleted; there is nothing left to compare
            if rec.get("label") and rec["label"] != current:
                print("note: %s cells are recorded as %r, but the route file now says %r "
                      "- the tables show the route file and say so"
                      % (route_name, rec["label"], route_label(load_route(route_name))))


def run_routes(run):
    """The routes this run covers, in the order it ran them: [(route, plan entry)].

    Read from the run's own record, so a summary describes what happened even after
    models.txt, routes/ or a resume changed underneath it. Sources, first seen wins:
    the plans in queued.json (superseded ones under "history" first, because a
    resume replaces the live plan with the routes *it* was started for), then any
    route directory that has cells but no plan entry.
    """
    root = run_root(run)
    names, by_name = [], {}
    path = os.path.join(root, "queued.json")
    if os.path.exists(path):
        try:
            plan = json.loads(read(path))
        except ValueError:
            plan = {}
        blocks = list(plan.get("history") or []) + [{"entries": plan.get("entries") or []}]
        for block in blocks:
            for e in block.get("entries") or []:
                name = e.get("route")
                if name and name not in by_name:
                    names.append(name)
                    by_name[name] = e
    if os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            if name in by_name or not os.path.isdir(os.path.join(root, name)):
                continue
            if any(os.path.exists(os.path.join(root, name, t, "meta.json")) for t in TASKS):
                names.append(name)
                by_name[name] = {}
    return [(n, by_name[n]) for n in names]


def run_label(run, route_name, entry=None):
    """Row name: the route file if it still exists, else the name the run recorded.

    A route can be deleted from routes/ after its cells ran (its model left pi's
    config); the row must still carry the name those cells ran under. The run's own
    plan comes before the cells because a cell records the label it was started
    with, and the plan may have been resolved more recently.
    """
    try:
        return route_label(load_route(route_name))
    except SystemExit:
        rec = recorded_config(route_dir(run, route_name)) or {}
        return (entry or {}).get("label") or rec.get("label") or route_name


def recorded_config(run_dir):
    """The config recorded by the first graded cell of this route, if any."""
    for task in TASKS:
        meta = os.path.join(run_dir, task, "meta.json")
        if os.path.exists(meta):
            try:
                return json.loads(read(meta))
            except ValueError:
                continue
    return None


def drift_reasons(recorded, info, route):
    """Why this route cannot be resumed as-is, if the settings moved under it.

    Resuming keys on meta.json existing, which means a changed sampler would be
    silently skipped -- you would think you re-ran with new temperatures and
    actually be reading the old cells. So compare what the finished cells used
    with what the route would send now and refuse instead.
    """
    reasons = []
    if recorded.get("model_pattern") != info["model_pattern"]:
        reasons.append("model %s -> %s" % (recorded.get("model_pattern"), info["model_pattern"]))
    if recorded.get("thinking") != route.get("thinking"):
        reasons.append("thinking %s -> %s" % (recorded.get("thinking"), route.get("thinking")))
    was = (recorded.get("route_sampling") or {}).get("samplingParams")
    now = (info.get("sampling") or {}).get("samplingParams")
    if was != now:
        reasons.append("sampling %s -> %s" % (json.dumps(was, sort_keys=True),
                                               json.dumps(now, sort_keys=True)))
    current = manifest_hash()
    if recorded.get("round_manifest") and current and recorded["round_manifest"] != current:
        reasons.append("the benchmark itself changed (MANIFEST.json hash differs)")
    return reasons


def snapshot_payload(run, entries):
    """The plan record a run writes once, when it starts."""
    return {"bench": BENCH, "run": run, "started": now(),
            "manifest_sha256": manifest_hash(),
            "runner_sha256": sha256(os.path.abspath(__file__)),
            "entries": entries}


def cell_processes():
    """pi processes still working on a cell of this benchmark (Linux /proc scan).

    Each cell is a `pi` child of the runner. If the runner dies, that child is
    orphaned: it keeps generating, holds the model, and writes into its cell dir,
    so a second run would fight it for the single loaded model.
    """
    root = os.path.join(bench_dir(), "runs") + os.sep
    found = []
    if not os.path.isdir("/proc"):
        return found
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open("/proc/%s/cmdline" % entry, "rb") as fh:
                argv0 = fh.read().split(b"\0", 1)[0].decode("utf-8", "replace")
            cwd = os.readlink("/proc/%s/cwd" % entry)
        except OSError:
            continue
        if cwd.startswith(root) and os.path.basename(argv0) == "pi":
            found.append((int(entry), cwd))
    return found


def install_stop_handler():
    """Make killing the runner kill its cell too, instead of orphaning it.

    If the signal lands in the window between spawning a cell and registering it,
    there is nothing in CELL_PROC to kill -- so fall back to the /proc scan and
    take out every cell of this benchmark before exiting. Only one runner is
    allowed to have cells here, so anything found is ours.
    """
    def stop(signum, frame):
        proc = CELL_PROC.get("proc")
        if proc is not None:
            print("\nstopping cell for signal %d ..." % signum, flush=True)
            terminate_cell(proc)
        else:
            stray = cell_processes()
            if stray:
                print("\nstopping %d untracked cell process(es) for signal %d ..."
                      % (len(stray), signum), flush=True)
                for pid, _cwd in stray:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except OSError:
                        pass
        sys.exit(130)
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, stop)
        except ValueError:
            pass


def plan_drift(entry, info):
    """Why the route's config no longer matches the plan this run recorded at start.

    cmd_run resolves every route up front and keeps that plan, so an edit to
    models.json or routes/*.json made while the run is going does NOT reach routes it
    has not started yet. That is deliberate -- every cell in a run comes from one
    resolved plan -- but it is invisible unless said out loud, so say it when the
    route is about to run.
    """
    reasons = []
    if entry.get("model_pattern") != info["model_pattern"]:
        reasons.append("model %s -> %s" % (entry.get("model_pattern"), info["model_pattern"]))
    was = entry.get("sampling")
    now = (info.get("sampling") or {}).get("samplingParams")
    if was != now:
        reasons.append("sampling %s -> %s" % (json.dumps(was, sort_keys=True),
                                              json.dumps(now, sort_keys=True)))
    return reasons


def cmd_run(args):
    run = args.name
    root = run_root(run)
    os.makedirs(root, exist_ok=True)

    stray = cell_processes()
    if stray and not os.environ.get("FORCE"):
        print("refusing to start: %d cell process(es) are already running under %s"
              % (len(stray), os.path.relpath(os.path.join(bench_dir(), "runs"), HERE)))
        for pid, cwd in stray:
            print("   pid %d  %s" % (pid, os.path.relpath(cwd, HERE)))
        print("   They hold the model, so a second run would fight them for the endpoint.")
        print("   Kill them with: kill -9 %s"
              % " ".join(str(pid) for pid, _ in stray))
        print("   (FORCE=1 skips this check, but two writers on one model is never a fair run.)")
        return
    install_stop_handler()
    queue = selected(args.routes)

    # Resolve every route up front and snapshot the plan, so the run records what
    # it was given even if models.txt, routes/ or models.json change later.
    plan = []
    for route_name, queue_cap in queue:
        route = load_route(route_name)
        rdir = route_dir(run, route_name)
        os.makedirs(rdir, exist_ok=True)
        info = resolve_route(route, rdir)
        plan.append((route_name, route, rdir, info, args.cap or queue_cap or DEFAULT_CAP))

    snapshot = os.path.join(root, "queued.json")
    entries = [{"route": n, "label": route_label(r), "cap_seconds": cap,
                "model_pattern": i["model_pattern"], "base_url": i.get("base_url"),
                "thinking": r.get("thinking"), "pi_model": r.get("pi_model"),
                "weights": route_weights(r),
                "sampling": (i.get("sampling") or {}).get("samplingParams")}
               for n, r, _d, i, cap in plan]
    if args.dry_run:
        print("== dry run: benchmark %s, run %s (nothing written, nothing executed)" % (BENCH, run))
    else:
        # queued.json is refreshed at every start, because cmd_run resolves the plan
        # afresh each time: the current file is what this run will actually use, and
        # the superseded plan is kept in history so nothing is lost.
        payload = snapshot_payload(run, entries)
        if os.path.exists(snapshot):
            stored = json.loads(read(snapshot))
            payload["started"] = stored.get("started") or payload["started"]
            history = list(stored.get("history") or [])
            if stored.get("entries") != entries:
                history.append({"replaced": stored.get("updated") or stored.get("started"),
                                "entries": stored.get("entries")})
                print("   note: the queue or route config changed since the last start;")
                print("         queued.json now records the current plan (the superseded one is in its history)")
            payload["history"] = history[-8:]
            print("== run %s in benchmark %s   (resuming; plan refreshed in %s)"
                  % (run, BENCH, os.path.relpath(snapshot, HERE)))
        else:
            print("== run %s in benchmark %s   (plan recorded in %s)"
                  % (run, BENCH, os.path.relpath(snapshot, HERE)))
        payload["updated"] = now()
        with open(snapshot, "w") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)

    calibration = None if args.dry_run else calibrate(root, force=args.recalibrate)
    if calibration:
        print("   gates   : " + ", ".join(
            "%s %.2fs" % (k, v["budget_seconds"])
            for k, v in sorted(json.loads(read(calibration))["gates"].items())))
        print("   cell cap: %s" % CELL_PROBE.get("mechanism", "not probed"))

    for route_name, route, rdir, info, cap in plan:
        print("== %s  (%s)" % (route_name, route_label(route)))
        fresh = resolve_route(route, rdir)
        changed = plan_drift(next((e for e in entries if e["route"] == route_name), {}), fresh)
        if changed:
            print("   note    : the config changed since this run started, and this run keeps its plan:")
            for reason in changed:
                print("             %s" % reason)
            print("             Cells for this route will use the recorded values above;")
            print("             use a new run name (--name <run>) to pick up the change.")
        print("   model   : %s%s" % (info["model_pattern"],
                                      "  thinking=" + route["thinking"] if route.get("thinking") else ""))
        print("   %s" % fmt_sampling(info))
        print("   cap     : %ds per cell, grading timeout %ds, memory caps %d MB (cell) / %d MiB (grade)"
              % (cap, GRADE_TIMEOUT, CELL_MEM_MB, GRADE_MEM_KB))
        recorded = recorded_config(rdir)
        reasons = drift_reasons(recorded, info, route) if recorded else []
        if reasons and not os.environ.get("FORCE"):
            print("   REFUSED : this run already has cells for %s, recorded with other settings:" % route_name)
            for reason in reasons:
                print("             %s" % reason)
            print("             Use a new run name (--name <run>), or FORCE=1 to overwrite the evidence.")
            continue
        if reasons:
            print("   FORCE=1 : overwriting %d recorded cell(s) for %s (%s)"
                  % (sum(1 for t in TASKS if os.path.exists(os.path.join(rdir, t, "meta.json"))),
                     route_name, "; ".join(reasons)))
        if args.dry_run:
            for task in TASKS:
                run_cell(route_name, route, info, rdir, task, cap, None, dry=True)
            continue
        for task in TASKS:
            run_cell(route_name, route, info, rdir, task, cap, calibration, dry=False)
        rows = [json.loads(read(os.path.join(rdir, t, "meta.json")))
                for t in TASKS if os.path.exists(os.path.join(rdir, t, "meta.json"))]
        if rows:
            passed = sum(1 for r in rows if r["grade"].get("ok"))
            print("   score   : %d/%d, %d out tokens, %d min"
                  % (passed, len(rows), sum(r["stats"]["out"] for r in rows),
                     sum(r["wall_seconds"] for r in rows) // 60))


def cmd_status(args):
    runs = [args.name] if args.name else list_runs()
    if not runs:
        print("no runs yet in benchmark %s - start one with: python3 run.py run --name <run>" % BENCH)
        return
    for run in runs:
        total = passed = 0
        print("run %s (benchmark %s)" % (run, BENCH))
        routes = run_routes(run) or [(n, {}) for n, _c in load_queue()]
        for route_name, _entry in routes:
            rdir = route_dir(run, route_name)
            marks = []
            for task in TASKS:
                meta = os.path.join(rdir, task, "meta.json")
                if not os.path.exists(meta):
                    marks.append(".")
                    continue
                m = json.loads(read(meta))
                ok = m["grade"].get("ok")
                marks.append("P" if ok else "F")
                total += 1
                passed += 1 if ok else 0
            score = "%d/%d" % (marks.count("P"), sum(1 for x in marks if x in "PF"))
            print("  %-24s %-12s %s%s" % (route_name, score, " ".join(marks),
                                           "  <- capped" if any(
                                               os.path.exists(os.path.join(rdir, t, "meta.json")) and
                                               json.loads(read(os.path.join(rdir, t, "meta.json"))).get("killed_at_cap")
                                               for t in TASKS) else ""))
        print("  total %d/%d cells graded" % (passed, total))
    print("(P pass, F fail, . not run; cell order %s)" % " ".join(TASKS))


def render_table(headers, rows):
    """A markdown table whose raw text also lines up.

    Markdown renderers ignore padding; terminals do not. And a delimiter row must
    have exactly as many cells as the header row -- an earlier version of this had
    six delimiters under seven headers, which is why it rendered as a wall of
    pipes. Cells are padded so the pipes line up in a plain terminal too.

    No column is aligned with ':' (---: / :---). Right-aligning the score and
    total columns made some renderers drop the cell borders on exactly those two
    columns, and the payoff -- numbers hugging the right edge -- is not worth a
    table that reads differently depending on the viewer.
    """
    rows = [[str(c) for c in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    def line(cells):
        return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"

    out = [line(headers), "|" + "|".join("-" * (w + 2) for w in widths) + "|"]
    out += [line(r) for r in rows]
    return "\n".join(out)


def sampler_table(run):
    """The sampler each route actually ran with.

    Rows come from the run's own record (run_routes), not from the live queue or
    from queued.json's current plan: a resume replaces that plan with the routes it
    was started for, and reading it left the table showing only the last resume's
    route while the score table showed the whole run.
    """
    keys = ["temperature", "top_p", "top_k", "min_p", "presence_penalty", "repeat_penalty"]
    short = {"presence_penalty": "presence", "repeat_penalty": "repeat"}
    headers = ["model", "sampling from"] + [short.get(k, k) for k in keys] + ["thinking", "cap"]
    rows = []
    for route_name, entry in run_routes(run):
        # recorded cells win over the start-of-run plan: they are what actually ran
        rec = recorded_config(route_dir(run, route_name)) or {}
        s = (rec.get("route_sampling") or {}).get("samplingParams") if rec else None
        if s is None:
            s = entry.get("sampling") or {}
        source = rec.get("route_sampling_source") or ("request" if s else "engine default")
        rows.append([run_label(run, route_name, entry), source]
                    + [s.get(k, "-") for k in keys]
                    + [rec.get("thinking") or entry.get("thinking") or "-",
                       "%ss" % (rec.get("cap_seconds") or entry.get("cap_seconds") or "-")])
    if not rows:
        return ""
    return render_table(headers, rows)


def kfmt(n):
    """Token counts, short: 147 -> '147', 6,097 -> '6.1k', 61,619 -> '61.6k'."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "-"
    return "%.1fk" % (n / 1000.0) if n >= 1000 else str(n)


def table_for(run):
    """One row per route in the run: verdict, wall clock and output tokens per task."""
    headers = ["model"] + TASKS + ["score", "out"]
    rows, caps = [], set()
    for route_name, entry in run_routes(run):
        rdir = route_dir(run, route_name)
        cells, label, total = [], run_label(run, route_name, entry), 0
        for task in TASKS:
            meta = os.path.join(rdir, task, "meta.json")
            if not os.path.exists(meta):
                cells.append("-")
                continue
            m = json.loads(read(meta))
            caps.add(m.get("cap_seconds"))
            st = m.get("stats") or {}
            out = st.get("out") or 0
            total += out
            mark = "P" if m["grade"].get("ok") else "F"
            # '+' on the token count = the last message never ended, so the count is a floor
            plus = "+" if st.get("partial_chars") else ""
            cells.append("%s%s %ss %s%s" % (mark, "*" if m["killed_at_cap"] else "",
                                            m["wall_seconds"], kfmt(out), plus))
        score = sum(1 for c in cells if c.startswith("P"))
        rows.append([label] + cells + ["%d/5" % score, kfmt(total)])
    note = "; ".join("`*` = killed at the %ss cap, file on disk graded afterwards" % c
                     for c in sorted(x for x in caps if x))
    return render_table(headers, rows), note


def cost_table(run):
    """What each route spent: output tokens, generation time, wall clock, the gap.

    Read from the same meta.json the score table reads, so the two cannot disagree
    about which cells they cover.

    `gen` is the sum of the completed assistant messages' durationMs, which includes
    prefill: `tok/s` is out/gen, "output tokens per unit of generation time", not
    decode speed. A long test-output history lowers it without the model decoding
    any slower. `tools` is wall - gen: pi startup, the model's own bash and test
    runs, and any final turn that never completed. That gap is the column that
    separates a fast model from a fast model that spends half an hour flailing.

    The rate is only meaningful inside one run: same host, same engine build, same
    sampler, cells run one at a time. Never compare it across runs -- a server under
    a different load or a different quant moves it. The `cells n/5` column is there
    so a partial route's aggregate is not read against a full one's.

    out/gen is sum over sum, not a mean of per-message rates: short messages are
    prefill-dominated, so the two disagree by a lot (ling-q8: 77.8 aggregate against
    a 56.9 median message) and the aggregate is the one that answers what the run
    cost. The printed footnote says nothing about this on purpose -- the formula
    beside it already states the weighting.
    """
    headers = ["model", "cells", "out", "gen", "wall", "tools", "tok/s"]
    rows = []
    for route_name, entry in run_routes(run):
        rdir = route_dir(run, route_name)
        out = gen_ms = wall = 0
        partial = False
        n = 0
        for task in TASKS:
            meta = os.path.join(rdir, task, "meta.json")
            if not os.path.exists(meta):
                continue
            m = json.loads(read(meta))
            st = m.get("stats") or {}
            n += 1
            out += st.get("out") or 0
            gen_ms += st.get("duration_ms") or 0
            wall += m.get("wall_seconds") or 0
            partial = partial or bool(st.get("partial_chars"))
        if not n:
            continue
        gen = int(round(gen_ms / 1000.0))
        # an old meta with no duration_ms is not "instantly generated": say nothing
        no_gen = gen_ms == 0
        rows.append([run_label(run, route_name, entry), "%d/%d" % (n, len(TASKS)),
                     kfmt(out) + ("+" if partial else ""),
                     "-" if no_gen else "%ds" % gen, "%ds" % wall,
                     "-" if no_gen else "%ds" % max(0, wall - gen),
                     "-" if no_gen or not out else "%.1f" % (out / (gen_ms / 1000.0))])
    if not rows:
        return "", ""
    note = ("`gen` = sum of completed assistant-message durations (prefill + decode); "
            "`tools` = wall - gen (pi startup, the model's own bash and test runs, "
            "unfinished final turns); `tok/s` = out / gen. One run, one host, one "
            "engine build: compare these rows with each other, never with another run.")
    return render_table(headers, rows), note


def models_table(run):
    """Provenance for the rows above: the weights, the drafter and the stack.

    Read from the run's own record first (the weights block written into each
    cell's meta.json and into the run's plan), because the question it answers is
    "what did this row run". A route file is only the fallback: routes/ is edited
    between runs and a route that left pi's config is deleted, and neither may
    change or delete a row of a run that already happened. The score table's names
    come from the same resolver, so the two tables cannot disagree about which
    model a row is.

    File paths, source repos and per-file caveats are deliberately not printed
    here: they stay in routes/<name>.json, which is already the record. Prose in a
    cell would wrap in a terminal and the continuation read like another row.
    """
    headers = ["model", "params", "quant", "GiB", "drafter", "arch (blocks / experts)",
               "ctx", "served by"]
    rows = []
    for route_name, entry in run_routes(run):
        rec = recorded_config(route_dir(run, route_name)) or {}
        m = rec.get("weights") or entry.get("weights") or {}
        if not m:
            try:
                m = route_weights(load_route(route_name))
            except SystemExit:
                m = {}
        if not m:
            rows.append([run_label(run, route_name, entry)] + ["-"] * (len(headers) - 1))
            continue
        d = m.get("drafter") or {}
        drafter = "-"
        if d.get("kind"):
            drafter = d["kind"]
            if d.get("quant"):
                drafter += " " + ("inline" if "inline" in d["quant"] else d["quant"])
            if d.get("size_gib"):
                drafter += " %.2f GiB" % d["size_gib"]
        arch = m.get("arch") or "-"
        if m.get("blocks"):
            arch += " %d blk" % m["blocks"]
        if m.get("experts"):
            arch += " / %d exp" % m["experts"]
            if m.get("experts_active"):
                arch += " (%d active)" % m["experts_active"]
        rows.append([m.get("name") or run_label(run, route_name, entry), m.get("params") or "-",
                     m.get("quant") or "-", "%.2f" % m["size_gib"] if m.get("size_gib") else "-",
                     drafter, arch, str(m.get("ctx") or "-"), m.get("stack") or "-"])
    return render_table(headers, rows)


def cmd_table(args):
    runs = [args.name] if args.name else list_runs()
    if not runs:
        print("no runs yet in benchmark %s" % BENCH)
        return
    for run in runs:
        table, cap_note = table_for(run)
        print("## run %s (benchmark %s)\n" % (run, BENCH))
        print(table)
        if cap_note:
            print("\n" + cap_note)
        costs, cost_note = cost_table(run)
        if costs:
            print("\n### cost\n")
            print(costs)
            print("\n" + cost_note)
        samplers = sampler_table(run)
        if samplers:
            print("\n### samplers\n")
            print(samplers)
        models = models_table(run)
        if models:
            print("\n### models\n")
            print(models)
        if args.write:
            out = os.path.join(bench_dir(), "RESULTS-%s.md" % run)
            body = "# Results: run %s (benchmark %s)\n\n%s\n\n%s\n" % (run, BENCH, table, cap_note)
            if costs:
                body += "\n### cost\n\n%s\n\n%s\n" % (costs, cost_note)
            if samplers:
                body += "\n### samplers\n\n%s\n" % samplers
            if models:
                body += "\n### models\n\n%s\n" % models
            with open(out, "w") as fh:
                fh.write(body)
            print("\nwrote %s" % os.path.relpath(out, HERE))
        print()


def cmd_stats(args):
    cell = args.cell
    print(json.dumps(stats(newest_session(cell)), indent=2, sort_keys=True))


def cmd_selftest(args):
    """Exercise the recording path without a model, in a temp directory.

    This exists because a rename in the recording code once passed py_compile and
    --dry-run, then killed a real run at the moment the first cell finished: the
    cell's work was on disk and nothing wrote a meta.json. A 20-line smoke test of
    exactly that path is cheaper than losing six minutes of a model's work.
    """
    import tempfile
    tmp = tempfile.mkdtemp(prefix="bench-selftest-")
    info = {"model_pattern": "selftest/model", "base_url": "http://127.0.0.1:1/v1",
            "sampling": {"samplingParams": {"temperature": 0.5}}}
    route = {"label": "selftest route", "thinking": "medium", "pi_model": "selftest/model"}
    try:
        fake_proc = subprocess.Popen([sys.executable, "-c", "pass"])
        fake_proc.wait()
        CELL_PROC["proc"] = fake_proc
        terminate_cell(fake_proc)                      # already exited: no-op path
        CELL_PROC["proc"] = None
        st = {"turns": 1, "out": 12, "reasoning": 3, "calls": {"read": 1}, "comp": 0,
              "rep_turns": 0, "duration_ms": 100, "last": "DONE", "partial_chars": 0,
              "source": "selftest"}
        meta = {"bench": BENCH, "run": "selftest", "route": "selftest", "label": route["label"],
                "task": TASKS[0], "model_pattern": info["model_pattern"],
                "route_file": "selftest.json", "base_url": info["base_url"],
                "route_sampling": info["sampling"], "warm_up": {"ok": True},
                "round_manifest": manifest_hash(), "runner_sha256": sha256(os.path.abspath(__file__)),
                "pi_version": pi_version(), "python": sys.version.split()[0],
                "host": os.uname().nodename, "cap_seconds": DEFAULT_CAP, "wall_seconds": 1,
                "killed_at_cap": False, "finished": finish_status(st), "grade": {"ok": True},
                "stats": st, "transcript": "", "solution_sha256": None, "calibration": None,
                "sampling": route.get("samplingParams"), "thinking": route.get("thinking"),
                "endpoint": None, "pi_model": route.get("pi_model"), "when": now()}
        path = os.path.join(tmp, "meta.json")
        with open(path, "w") as fh:
            json.dump(meta, fh, indent=2, sort_keys=True)
        line = format_line(json.loads(read(path)))
        drift = drift_reasons(meta, info, route)
        snapshot_payload("selftest", [])
        print("recording path OK")
        print("  meta round-trips: %s" % (json.loads(read(path))["task"] == TASKS[0]))
        print("  log line        : %s" % line)
        print("  no drift for the same config: %s" % (drift == []))
    except Exception as e:
        print("recording path BROKEN: %s: %s" % (type(e).__name__, e))
        raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ live view

RESET = "\033[0m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
BOLD = "\033[1m"


class Live(object):
    """Renders a pi event stream while it is being written.

    Reads the cell's pi.jsonl (the runner's stdout capture), which carries
    token-level deltas plus tool start/end events, so a running cell can be
    watched the way the interactive UI shows it.
    """

    def __init__(self, path, color=True):
        self.path = path
        self.pos = 0
        self.partial = ""
        self.color = color
        self.open_line = False
        self.turns = 0
        self.tools = 0
        self.out = 0
        self.reasoning = 0
        self.started = time.time()
        self.kind = None
        self.tool_name = None
        self.tool_args = ""
        self.style_code = None

    def c(self, text, code):
        return code + text + RESET if self.color else text

    def write(self, text, style=None):
        """Write text, switching ANSI style only when it actually changes."""
        if self.color and style != self.style_code:
            sys.stdout.write(RESET + (style or ""))
            self.style_code = style
        sys.stdout.write(text)
        sys.stdout.flush()
        self.open_line = not text.endswith("\n")

    def end_line(self):
        if self.open_line:
            self.write("\n")
        self.style_code = None

    def header(self):
        parts = self.path.split(os.sep)
        task = parts[-2]
        route = parts[-3]
        run = parts[-4] if len(parts) >= 4 and parts[-4] != "runs" else "-"
        try:
            age = time.time() - os.stat(self.path).st_ctime
        except OSError:
            age = 0
        self.style_code = None
        print("\n%s" % self.c("── %s / %s / %s   (started %ds ago) %s" %
                              (run, route, task, int(age), "─" * 20), BOLD), flush=True)

    def footer(self):
        self.style_code = None
        print(self.c("   [%4ds  turns=%d  tools=%d  out=%d tok  reasoning=%d tok]" %
                     (time.time() - self.started, self.turns, self.tools, self.out, self.reasoning), DIM),
              flush=True)

    def render(self, rec):
        t = rec.get("type")
        if t == "message_update":
            ev = rec.get("assistantMessageEvent") or {}
            kind = ev.get("type") or ""
            if kind.endswith("_start"):
                self.kind = kind.split("_")[0]
                self.end_line()
                if self.kind == "thinking":
                    self.write("· thinking: ", DIM)
                elif self.kind == "toolcall":
                    self.write("→ %s " % (ev.get("toolName") or "tool"), CYAN)
                    self.tool_name = ev.get("toolName") or "tool"
                    self.tool_args = ""
            elif kind.endswith("_delta"):
                delta = ev.get("delta") or ""
                if self.kind == "thinking":
                    self.write(delta, DIM)
                elif self.kind == "toolcall":
                    self.tool_args += delta
                    if len(self.tool_args) <= 160:
                        self.write(delta.replace("\n", " "), CYAN)
                else:
                    self.write(delta)
            elif kind == "toolcall_end":
                self.tools += 1
                args = (ev.get("toolCall") or {}).get("arguments") or {}
                self.end_line()
                self.write("  " + self.c(describe_call(self.tool_name, args), DIM) + "\n")
                self.style_code = None
            elif kind == "text_end":
                if not str(ev.get("content") or "").endswith("\n"):
                    self.write("\n")
            elif kind.endswith("_end"):
                self.end_line()
            return
        if t == "tool_execution_end":
            res = rec.get("result") or {}
            text = res.get("structuredContent")
            if text is None:
                for block in res.get("content") or []:
                    text = block.get("text") or text
            text = (str(text) if text is not None else "").strip().splitlines()
            first = text[0][:110] + ("..." if text and len(text[0]) > 110 else "")
            extra = " (+%d lines)" % (len(text) - 1) if len(text) > 1 else ""
            self.end_line()
            self.write("  ← %s%s  %sms\n" % (first or "(empty)", extra, rec.get("durationMs")),
                       RED if rec.get("isError") else DIM)
            self.style_code = None
            return
        if t == "turn_end":
            msg = rec.get("message") or {}
            usage = msg.get("usage") or {}
            self.turns += 1
            self.out += usage.get("output") or 0
            self.reasoning += usage.get("reasoning") or 0
            self.end_line()
            self.footer()
            return
        if t == "agent_end":
            self.end_line()
            self.write("   [agent finished]\n", GREEN)
            self.style_code = None
            return

    def feed(self, chunk):
        data = self.partial + chunk
        lines = data.split("\n")
        self.partial = lines.pop()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            try:
                self.render(rec)
            except Exception as e:            # a live view must never die on one bad record
                self.end_line()
                self.write(self.c("   [render error: %s]\n" % e, RED))
            print("", end="")                 # keep output flowing on buffered pipes


def describe_call(name, args):
    if not isinstance(args, dict):
        return "%s %s" % (name, str(args)[:80])
    if name == "bash":
        return "bash: %s" % str(args.get("command", ""))[:160]
    path = args.get("path") or args.get("file_path") or args.get("filePath")
    if name == "write":
        body = args.get("content") or ""
        return "write %s (%d chars)" % (path, len(body))
    if name in ("read", "ls", "find") and path is not None:
        return "%s %s" % (name, path)
    if name == "edit":
        return "edit %s" % path
    if name == "grep":
        return "grep %r" % args.get("pattern")
    return "%s %s" % (name, json.dumps(args, sort_keys=True)[:140])


def active_streams(run=None):
    """Cell event streams, newest first. With a run name, only that run's."""
    root = os.path.join(bench_dir(), "runs")
    if run:
        root = os.path.join(root, run)
    found = []
    for dirpath, _dirs, names in os.walk(root):
        if "pi.jsonl" in names:
            found.append(os.path.join(dirpath, "pi.jsonl"))
    return sorted(found, key=os.path.getmtime, reverse=True)


def cmd_watch(args):
    target = args.cell
    if target and os.path.isdir(target):
        target = os.path.join(target, "pi.jsonl")
    use_color = args.color or (not args.no_color and sys.stdout.isatty())
    live = None
    seen_meta = set()
    last_notice = 0.0
    while True:
        path = target
        if not path:
            streams = [p for p in active_streams(args.name)
                       if time.time() - os.path.getmtime(p) < (args.idle_after or 180)]
            path = streams[0] if streams else None
        if path != (live.path if live else None):
            if live:
                live.end_line()
                live.footer()
            live = Live(path, color=use_color) if path else None
            if live:
                live.header()
        if live and os.path.exists(live.path):
            with open(live.path, errors="replace") as fh:
                fh.seek(live.pos)
                chunk = fh.read()
                live.pos = fh.tell()
            if chunk:
                live.feed(chunk)
                last_notice = 0.0
            meta = os.path.join(os.path.dirname(live.path), "meta.json")
            if os.path.exists(meta) and meta not in seen_meta:
                seen_meta.add(meta)
                try:
                    live.end_line()
                    print(format_line(json.loads(read(meta))), flush=True)
                except ValueError:
                    pass
                if args.once:
                    return
        if args.once and live and live.pos:
            return
        if not live and time.time() - last_notice > (0 if last_notice == 0.0 else 30):
            where = ("run %s" % args.name) if args.name else "any run"
            print("no cell is running for %s; waiting - looked in %s"
                  % (where, os.path.join(bench_dir(), "runs")), flush=True)
            last_notice = time.time()
        time.sleep(0.5)


def main():
    global BENCH, RUN
    try:
        sys.stdout.reconfigure(line_buffering=True)   # detached logs must appear as they happen
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--bench", default=None,
                        help="benchmark directory to run against (default %s; available: %s)"
                             % (BENCH, ", ".join(list_benchmarks()) or BENCH))
    common.add_argument("--name", default=None,
                        help="name of the run inside that benchmark (run defaults to %s)"
                             % DEFAULT_RUN)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, help_ in (("check", cmd_check, "probe each queued route with one turn"),
                            ("run", cmd_run, "walk the queue as a named run"),
                            ("status", cmd_status, "per-run progress (all runs, or --name)"),
                            ("table", cmd_table, "results table per run"),
                            ("runs", None, "list the runs in a benchmark")):
        p = sub.add_parser(name, help=help_, parents=[common])
        if name in ("check", "run"):
            p.add_argument("routes", nargs="*", help="route names (default: all of models.txt)")
        if name == "run":
            p.add_argument("--cap", type=int, default=None, help="seconds per cell")
            p.add_argument("--dry-run", action="store_true")
            p.add_argument("--detach", action="store_true", help="re-exec detached and return")
            p.add_argument("--recalibrate", action="store_true")
        if name == "table":
            p.add_argument("routes", nargs="*")
            p.add_argument("--write", action="store_true", help="write RESULTS-<run>.md")
        if fn is None:
            p.set_defaults(fn=lambda a: [print(r) for r in list_runs()]
                           or print("(benchmark %s; %s)" % (BENCH, ", ".join(list_benchmarks()))))
        else:
            p.set_defaults(fn=fn)
    p = sub.add_parser("stats", help="one cell's parsed stats", parents=[common])
    p.add_argument("cell")
    p.set_defaults(fn=cmd_stats)
    p = sub.add_parser("selftest", help="smoke-test the recording path (no model needed)",
                       parents=[common])
    p.set_defaults(fn=cmd_selftest)
    p = sub.add_parser("watch", help="live transcript view of a running cell", parents=[common])
    p.add_argument("cell", nargs="?", help="cell dir (default: the newest stream, or --name's run)")
    p.add_argument("--once", action="store_true", help="render what is there and exit")
    p.add_argument("--no-color", action="store_true")
    p.add_argument("--color", action="store_true", help="force color when piping")
    p.add_argument("--idle-after", type=int, default=180,
                   help="seconds after which a stream counts as not running (default 180)")
    p.set_defaults(fn=cmd_watch)
    args = ap.parse_args()

    BENCH = args.bench or BENCH
    if args.cmd == "run":
        args.name = args.name or DEFAULT_RUN     # the conventional first run
    RUN = args.name

    if args.cmd == "run" and args.detach:
        log = os.path.join(HERE, "runner-%s-%s.log" % (BENCH, args.name))
        argv = [sys.executable, os.path.abspath(__file__), "run", "--bench", BENCH, "--name", args.name]
        argv += args.routes
        if args.cap:
            argv += ["--cap", str(args.cap)]
        with open(log, "a") as fh:
            proc = subprocess.Popen(argv, stdout=fh, stderr=subprocess.STDOUT,
                                    start_new_session=True)
        print("detached pid %d, logging to %s\npoll with: python3 run.py status --name %s"
              % (proc.pid, os.path.relpath(log, HERE), args.name))
        return
    args.fn(args)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        # e.g. `run.py status | head` -- closed pipe is not an error
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(0)
