# coding-bench

Five hard coding tasks, run agentically against any model that pi can reach, graded
by tests the model never sees. Built for one question: given a complete spec, an
empty directory and the tools a coding agent normally has, does the model end up
with a file that actually works?

Each cell gives the model a single spec file (`TASK.md`), a fresh directory, and a
1800-second cap. It has to write `solution.py` and its own `test_solution.py`, run
its tests, and stop. Grading then happens outside its view: fixed cases from the
spec, hundreds of randomized cases checked against a brute-force oracle, and — for
the three tasks where the spec names one — a performance gate.

- `README.md` (this file) — what it is, how to run it, what gets recorded.
- `RUN-WITH-PI.md` — the prompt to hand to a coding agent to make it run the suite.
- `A/` — the benchmark: sealed specs, prompts, graders, references, and its runs.
  - `A/runs/<name>/` — one named run (experiment) and its evidence.
  - `A/RESULTS-<name>.md` — that run's table. `A/MANIFEST.json` seals the instrument.

## The five tasks

| id | what the model must implement | gate |
|---|---|---|
| `c1_csv_line` | CSV record parser: quotes, doubled quotes, empty fields, the spec's error cases | — |
| `c2_eval_expr` | arithmetic expression evaluator: precedence, `^`, unary minus, errors as specified | — |
| `c3_tokenize` | shell-like tokenizer: quoting, escapes, comments, raw backslashes | 200k-character line |
| `c4_schedule` | interval scheduling: maximum profit, fewest intervals, lexicographic tie-break | 200k intervals, twice |
| `c5_shortest_match` | shortest-prefix matcher for a pattern language with `*`, `?`, `{a,b}`, escapes | 20 stars, 4000 chars |

In a little more detail:

- **`c1_csv_line`** splits one CSV record into fields under the spec's own quoting rules
  rather than Python's `csv` module: a field is quoted only when the quote is its first
  character, `""` inside a quoted field is one literal quote, and a quote anywhere else is
  an ordinary character. It must raise `ValueError` for an unterminated quoted field, and
  for anything between a closing quote and the next comma or the end of the line.
- **`c2_eval_expr`** evaluates `+ - * / ^` with unary signs and parentheses and always
  returns a float. The exceptions are pinned: `ZeroDivisionError` propagates from the
  division, an unrepresentable value raises `OverflowError` (`2^5^5`), and a negative base
  with a fractional exponent raises `ValueError` (`(-8)^0.5`) instead of returning a
  complex number.
- **`c3_tokenize`** splits a command line the way a POSIX shell does: whitespace separates
  tokens, adjacent segments (`bare`, `'single'`, `"double"`) concatenate into one token,
  and an empty segment still creates a token. Backslashes escape one character, and `#`
  starts a comment only at the start of a token, so `a#b` is one token but `a #b` is one
  token and a comment.
- **`c4_schedule`** picks non-overlapping intervals from up to 200,000 candidates,
  maximizing total profit, then minimizing the number of intervals, then choosing the
  lexicographically smallest list in the spec's ordering. Touching intervals (`end ==
  start`) do not overlap. The gate runs two shapes at 200,000 intervals each, and a DP over
  all pairs of intervals will not meet it.
- **`c5_shortest_match`** returns the length of the shortest prefix a pattern can match,
  for a language of literals, `?` (one character), `*` (zero or more), `{a,bc}` groups and
  backslash escapes, with malformed patterns raising `ValueError`. The gate is twenty
  stars against a 4,000-character text, which is where a backtracking or `re`-based matcher
  falls over.

The specs are complete on purpose: everything the grader tests is stated in
`TASK.md`, including error types, tie-breaks and raw-character conventions. A model
that follows the spec literally passes; a model that improvises the usual Python
idioms for these problems usually fails somewhere specific.

## Requirements

- Python 3.8+ with the standard library only (the runner and the graders use
  nothing else).
- `pi` on `PATH`, version 1.2.0 or newer: the runner passes flags such as
  `--no-skills`, `--no-mcp` and `--no-approve` that older versions do not have.
  `MANIFEST.json` records the version the round was sealed with.
- The same host tools the prompts use: `timeout`, `setsid`-style detachment, and a
  Linux or macOS userland (`os.uname`, `resource`).
- A model endpoint: a local llama.cpp / Ollama / vLLM server, or a cloud provider
  pi is configured for. One model resident at a time is enough.

## Quick start

```sh
python3 A/validate.py                 # graders vs references: expect 22 passed
cp routes/example.json routes/mymodel.json    # edit: endpoint, model id, sampling
$EDITOR models.txt                    # put mymodel in the queue
python3 run.py check mymodel           # one warm-up + one cheap turn; want "ok"
python3 run.py run --name baseline --detach   # walk the queue as a named run
python3 run.py watch                   # live view of whichever cell is running
python3 run.py status                  # per-run progress (all runs, or --name)
python3 run.py table --write           # A/RESULTS-<run>.md from the evidence
```

Run `run --detach` and `watch` in two terminals (or two panes): the runner needs
to outlive your shell, and watching is how you see what the model is doing.

## Results: benchmark A, run `baseline`

Nine models, five cells each, one sample per cell, 1800-second cap, on one RX 9060 XT
(16 GB) with pi 1.2.0. Four models cleared all five tasks; the two heaviest tasks decided
the rest.

| model                                                                     | c1_csv_line     | c2_eval_expr    | c3_tokenize    | c4_schedule   | c5_shortest_match | score | out    |
|---------------------------------------------------------------------------|-----------------|-----------------|----------------|---------------|-------------------|-------|--------|
| Qwen3.8-27B (ASCII-Condensed) UD-IQ4_XS + MTP (kv-stream fork, 98304 ctx) | P 147s 6.1k     | P 1733s 61.6k   | P 722s 29.9k   | P 791s 32.0k  | P 671s 27.7k      | 5/5   | 157.4k |
| Qwen3.8-Flash-Next GSQ-RCO Coder IQ1_M (PolyStrata, 98304 ctx)            | P 592s 23.6k    | P 316s 12.7k    | P 485s 18.3k   | P 350s 13.0k  | P 738s 26.7k      | 5/5   | 94.4k  |
| Qwen3.8-27B IQ3_XXS + MTP (llama.cpp router, 65536 ctx)                   | P 223s 6.7k     | F* 1800s 40.2k+ | P 1715s 40.2k  | F* 1800s 45+  | P 1588s 37.9k     | 3/5   | 125.1k |
| Swift-1.5-Qwen3.8-27B GSQ-RCO IQ3_XXS + MTP (llama.cpp router, 98304 ctx) | P 360s 10.9k    | P 441s 13.6k    | P* 1800s 39.1k | P 1095s 31.8k | P 1292s 30.1k     | 5/5   | 125.4k |
| Qwen3.6-35B-A3B REAP-48 v2 Q4_K_M + DFlash (llama.cpp router, 131072 ctx) | P 276s 10.8k    | P 358s 15.5k    | P 532s 22.1k   | F 453s 22.4k  | F 1076s 44.3k     | 3/5   | 115.2k |
| Qwen3.6-35B-A3B UD-Q4_K_M (PolyStrata, 131072 ctx)                        | P 903s 35.7k    | F 542s 26.1k    | P 135s 5.7k    | F 1090s 42.8k | F* 1800s 78+      | 2/5   | 110.4k |
| Ornith-1.5-35B Q4_K_M (PolyStrata, 131072 ctx)                            | P 59s 3.7k      | P 84s 5.5k      | P 193s 11.1k   | P 723s 34.5k  | P 299s 17.4k      | 5/5   | 72.3k  |
| Mellum2.1-12B-A2.5B-Thinking Q6_K (llama.cpp router, 131072 ctx)          | F 706s 45.4k    | P 209s 15.8k    | F 302s 22.2k   | F 274s 20.3k  | F 395s 27.9k      | 1/5   | 131.6k |
| LFM2.5-24B-A2B Q6_K (PolyStrata, 131072 ctx)                              | F* 1800s 61.6k+ | P 979s 39.3k    | F 1114s 42.1k+ | F 489s 22.9k  | F* 1800s 57.6k+   | 1/5   | 223.5k |

`*` = killed at the 1800s cap, file on disk graded afterwards

Reading it: the task set does not separate models by size. Ornith-1.5-35B takes 5/5 for
72k output tokens, while LFM2.5-24B-A2B spends 224k — three times as much — for 1/5, and
Mellum2.1-12B (132k) also lands at 1/5. `c4_schedule` and `c5_shortest_match` are where
models fail most (5 and 4 of the nine), and both are the tasks with a property the spec
states and a naive solution ignores: c4's tie-break, c5's non-backtracking matcher.
`c1` and `c3` each cost two models a point, and in every case on an error path the spec
spells out — a missing `ValueError` rather than a wrong algorithm.

One sample per cell is a real limit. Earlier runs of this suite against the same weights
have flipped cells both ways, so treat a single point as a draw from a distribution, not a
verdict. Per-cell detail, the samplers each model ran under, and the weights table are in
`A/RESULTS-baseline.md` — regenerate it with `python3 run.py table --name baseline --write`.

## Benchmarks and runs


The repository separates two things that are easy to confuse:

- **A benchmark** (`A/`, and later `B/`) is the sealed instrument: the task specs,
the prompts, the graders, the gates. It has a `MANIFEST.json` hashing all of them.
- **A run** is one named experiment inside a benchmark: `A/runs/<name>/<route>/<task>/`.

The point of named runs is that you can run the queue, change a sampler or a
thinking level, and run the queue again without the two mixing. `--name` selects
the run, `--bench` selects the benchmark (default `A`):

```sh
python3 run.py run --name baseline        # per-model recommended samplers
$EDITOR ~/.pi/agent/models.json           # change a temperature
python3 run.py run --name temp-0.6        # a second, separate experiment
python3 run.py status                     # both runs side by side
python3 run.py table --name baseline --write
```

Two guards make that safe:

- **Changing the settings does not silently reuse old cells.** Resuming keys on a
  cell's `meta.json` existing, so a changed sampler would otherwise be *skipped* —
  you would think you re-ran with the new temperatures and actually be reading the
  old results. The runner compares each route's recorded settings (model, sampler,
  thinking level, and the benchmark's manifest hash) with what the route would send
  now and **refuses** that route if they differ. To overwrite deliberately, use a
  new run name or `FORCE=1`.
- **An orphaned cell does not get to fight the next run.** Each cell is its own
  `pi` process in its own session. If the runner dies without stopping it (a
  `kill -9`, or the desktop session going down), that cell keeps generating and
  keeps holding the model. The runner kills its cell on SIGINT/SIGTERM — escalating
  to SIGKILL, because `pi` ignores SIGTERM — and it refuses to start when a cell
  process is still alive under the benchmark, printing the pid so you can deal with
  it.

- **Each run records the plan it was given.** `A/runs/<name>/queued.json` holds the
  route list, resolved model ids, base URLs, samplers, thinking levels and caps as
  they were at start, so a run stays self-describing after you edit `models.txt`,
  `routes/*.json` or `models.json`.

Routes come in two forms:

- **endpoint** (`routes/example.json`): `baseUrl`, `api`, `apiKey`, model id,
  context, `samplingParams`. The runner writes a scratch pi config directory for
  the run, so the sampling and context you see in the route file are what actually
  went on the wire, and nothing in your own `~/.pi/agent` is touched.
- **`pi_model`** (`routes/qwen38-fork.json`): reuse an entry that already exists in
  your `models.json`. Less to configure, less recorded: the runner reads your
  `models.json` to log which base URL and sampling that entry implies.

Use the endpoint form when you want the run to be reproducible from this
repository alone.

Both forms should carry a **`weights`** block: which model file the route runs.

```json
"weights": {
  "name": "Qwen3.6-35B-A3B REAP-48 v2", "params": "35B-A3B", "quant": "Q4_K_M",
  "arch": "qwen35moe", "blocks": 40, "experts": 133, "experts_active": 8,
  "file": "models/Qwen3.6-35B-A3B-REAP-48-v2/Qwen3.6-35B-A3B-REAP-48-v2.gguf",
  "size_gib": 8.78,
  "source": "REAP-48 prune of Qwen3.6-35B-A3B; the pruner's repo is not recorded",
  "drafter": {"kind": "DFlash", "quant": "Q6_K", "file": "...", "size_gib": 0.31},
  "stack": "llama.cpp router", "stack_id": "Qwen3.6-35B-A3B-REAP-48-v2", "ctx": 131072,
  "serve": {"cache_k": "bf16", "cache_v": "bf16", "batch": "1024/1024",
            "spec": "draft-dflash, n-max 3"}
}
```

The block is called `weights`, not `model`, because an endpoint route already uses
`model` for the endpoint's own entry (`id`, `contextWindow`, `maxTokens`).

The display name in the score table is composed from that block (`name`, plus
`drafter.kind`, plus `stack` and `ctx`), so the table cannot disagree with the record.
It was free text before, and of the nine routes three had dropped their quant and one
had never been named at all. `run.py table --write` also emits a `### models` table
(quant, size, drafter, architecture, context) beyond the `### samplers` one, so a results
file says what the weights were and what sampler they ran under. Neither table carries prose: file
paths, source repos and per-file caveats stay in `routes/<name>.json`, because a
sentence in a cell wraps in a terminal and the continuation reads like another row. Rename a route after its
cells ran and the table shows the route file's name while saying that the cells were
recorded under the old one, instead of mixing the two silently.

Note the `sampling from` column in `run.py table`: `request` means pi sends the values
shown (they are in `meta.json` too), `engine default` means the entry carries no
`samplingParams` so nothing is sent and the server decides. On this box that is
llama.cpp's built-ins — temperature 0.80, top_k 40, top_p 0.95, min_p 0.05,
repeat_penalty 1.00 — unless the model's GGUF metadata or launch flags override them.
No route is in that state at the moment: Mellum2.1-12B was the last one, and it now
sends its card's agentic sampler explicitly (temperature 1.0, top_p 0.95, top_k 20).

Round A runs each model at its **own recommended thinking-mode sampler** rather than
one shared preset: `samplingParams` lives on the model entry (or in the route file for
endpoint routes), `run.py run` prints the resulting sampler in its header, `run.py check`
prints it per route, and every cell's `meta.json` records it. Note the keys differ by
engine: llama.cpp's server field is `repeat_penalty` (it has no `repetition_penalty`),
while PolyStrata accepts both names, so this repository uses `repeat_penalty`
everywhere. A field that is *absent* from the request falls back to the server's or the
model config's default, which is why "make it explicit" is not the same as "leave it".

## Watching a run

`python3 run.py watch` attaches to the cell that is running right now and streams it,
which is the closest thing here to the interactive UI:

```
── qwen38-fork / c1_csv_line   (started 42s ago) ────────────────────
· thinking: Let me start by reading TASK.md.
→ read {"path":"TASK.md"}
  read TASK.md
  ← # CSV record parser (+57 lines)  2ms
   [   1s  turns=1  tools=1  out=38 tok  reasoning=0 tok]
→ write /…/c1_csv_line/solution.py
  write /…/c1_csv_line/solution.py (2140 chars)
→ bash: python3 test_solution.py
  ← 4 passed  1.2s
   [  96s  turns=6  tools=8  out=3114 tok  reasoning=902 tok]
```

Thinking is dim, tool calls cyan with their arguments, results dim with the first
line plus a line count, and a footer after each turn with elapsed time, turns,
tool calls and tokens. When the cell finishes, the runner's own verdict line is
printed, and the view follows on to the next cell automatically.

`python3 run.py watch <cell-dir>` pins it to one cell (useful with `--once` to
dump a finished cell's transcript), `--no-color` is for pipes and logs, and
`--idle-after` controls how old a stream may be before it counts as not running.

One caveat it will show you honestly: pi's session file (and therefore the token
totals in `meta.json` and `run.log`) only contains *completed* messages, so a cell
killed mid-message loses that message's usage. Those lines carry
`partial=<chars>c`, the number of characters that were streamed after the last
completed turn, so a cell showing `out=38 … partial=13678c` is not a cell that
said 38 tokens — it is a cell whose last message never ended.

## What gets recorded

Per run: `run.log`, `queued.json` (the plan as started) and `calibration.json`
(this machine's gate budgets). Per cell, `A/runs/<run>/<route>/<task>/`:

- `TASK.md`, `solution.py`, `test_solution.py` — what the model saw and produced.
- `sessions/*.jsonl` — the full transcript, including thinking blocks.
- `pi.jsonl`, `pi.err` — the event stream and stderr.
- `meta.json` — route, resolved base URL and sampling, manifest hash, runner hash,
  `pi --version`, Python version, host, cap, warm-up, wall clock, whether the cap
  fired, the model's own last words (`DONE` / `BLOCKED` / unfinished), parsed stats
  (turns, output and reasoning tokens, tool-call histogram, compactions, repetition
  turns, and the unrecorded-output figure `partial_chars`), the grade JSON, and
  SHA-256 of the solution and the transcript.

Per run: `run.log` (one generated line per cell), `calibration.json` (this machine's
gate budgets) and `queued.json`, which holds the plan including each route's `weights`
block, so the plan of a finished run still says which weights it was going to use.
`.pi-config/` appears when an endpoint route was used. Per benchmark: `MANIFEST.json`
(SHA-256 of every sealed file) and `RESULTS-<run>.md` per run.

What this repository keeps from a run, and what it does not: `meta.json`,
`solution.py` and `test_solution.py` are committed, so the grades and the code the
models wrote can be inspected. The transcripts (`pi.jsonl`, `sessions/`) are ignored —
they run to hundreds of megabytes — and their SHA-256 is in `meta.json` either way.

## Performance gates are calibrated, not absolute

A gate must not fail a correct solution because the grading machine is slow, so
each gate is a multiple of what the bundled reference solution costs *on that
machine*, timed by `A/checks.py --calibrate` at the start of every model run:

| gate | multiple | floor |
|---|---|---|
| `c3_200k_line` | 6.0× | 3.0 s |
| `c4_200k_intervals` | 6.0× | 3.0 s |
| `c4_200k_identical` | 6.0× | 3.0 s |
| `c5_20_stars` | 4.5× | 10.0 s |

`budget = max(multiple × reference_seconds, floor)`. The floors are the absolute
budgets an earlier fixed version of this suite used, so a machine faster than the
reference is never graded more harshly than before, and a gate whose reference is
tiny (c3's reference is 0.02 s) stays a check on algorithmic complexity rather than
on timer noise. Every verdict says which bound applied:

```
200k intervals in 0.52s (1.01x ref, budget 6.0x = 3.11s)   PASS
20 stars in 2.27s (0.98x ref, budget 4.5x = 10.17s)         PASS
200k character line in 0.02s (no calibration; absolute budget 3.00s)
```

A result within 15% of a budget is labelled `marginal`, because a single sample at
the edge flips on scheduler noise.

## The cap, and how capped cells are marked

`run.py` runs each cell under `timeout`-equivalent handling: SIGINT at the cap, then
SIGKILL. Whatever is on disk is graded afterwards, so a runaway cell costs its cap
instead of the whole run. Capped cells are marked with `*` in `RESULTS-<run>.md` and carry
`"killed_at_cap": true` plus the model's own last words in `meta.json` — `P*` and
`F*` distinguish "passed, but was still polishing when the cap fired" from "ran out
of time and failed anyway".

Use the same cap for every model you intend to compare.

## Resource limits

Two memory caps, enforced differently because they cover different things:

- **The cell: 4 GB, physical, via a systemd user scope.** Each cell runs as
  `systemd-run --user --scope --quiet -p MemoryMax=4096M -p MemorySwapMax=0 -- pi ...`,
  so the model's own tools and test scripts are inside the cap too. Exceeding it
  OOM-kills inside that cgroup, not on the desktop. This is the cap that matters:
  solutions here need megabytes (the c5 reference passes under 256 MB), but models do
  write pattern fuzzers that grow without bound, and on this box the serving engine can
  be holding 20 GB at the same time. `meta.json` records the cap and mechanism per cell.

  One measured caveat: the kernel chooses its own victim inside the cgroup. When the
  memory is page cache rather than a process's heap — a `pi` bash log landing in a tmpfs
  `/tmp` because a solution prints in an infinite loop — it killed `pi` itself, at
  139 MB, and that cell ended with no `meta.json` and no `run.log` line. The desktop
  survived; the cell's record did not. A per-cell private mount namespace with a
  size-bounded tmpfs turns that into a legible `ENOSPC`, and is the next change here.
- **Grading: 3 GB, virtual, via `RLIMIT_AS`.** `checks.py` is plain Python, so an
  address-space cap is fine there — and it is what stops a candidate solution that
  compiles the pattern to a backtracking `re` from consuming 7 GB.

Why not `RLIMIT_AS` for the cell as well: it limits *virtual* space, and Node
reserves enough of it that undici's WASM `llhttp` fails to instantiate
(`RangeError: WebAssembly.instantiate(): Out of memory`) and `pi` dies before the
model is ever called. A physical cap has no such problem: `pi` runs at ~66 MB and
a runaway script is killed at the limit.

If `systemd-run` is unavailable the runner starts the cell uncapped and records
`cell_mem_mechanism: none`, so the evidence never claims a cap that was not there.

## What is reproducible, and what is not

Sealed per round: the specs, both prompts, the tool allowlist, the graders, the
randomized-case seeds (five fixed constants), the reference solutions, and the gate
policy. `MANIFEST.json` hashes all of them, and each `meta.json` records that hash
plus the runner's own hash, so a cell can be re-checked later without trusting the
checkout.

Not reproducible by design: model output. Weights, quantization, sampler, backend
and host all change the tokens. So this repository ships the *instrument*, and the
results table is per-machine: run it on your hardware and you get your own table,
comparable to another machine's table in scores and in token cost, not in
bit-identical transcripts.

Runs are hermetic in the other direction: `--no-context-files --no-skills
--no-extensions --no-prompt-templates --no-mcp --no-themes --no-approve --offline`,
an explicit `--tools` allowlist, an explicit `--append-system-prompt`, and (for
endpoint routes) a scratch `PI_CODING_AGENT_DIR`. Your own skills, extensions,
`AGENTS.md` and project files cannot leak into a cell.

## Starting a new benchmark

Copy the benchmark directory (`A/` → `B/`), give it different tasks, prompts or
graders, regenerate `MANIFEST.json`, and clear `runs/`. Benchmarks are independent
and self-contained on purpose: one that quietly inherits a grader change from
another is not a measurement anymore. Each benchmark keeps its own runs, so
`python3 run.py run --bench B --name baseline` is a different experiment in a
different instrument. When you change a spec's wording, say so in that benchmark's
results — the spec is part of the instrument.
