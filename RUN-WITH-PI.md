# Run this benchmark with pi

Copy the prompt below into a fresh `pi` session that is sitting in a checkout of
this repository. It is written for the agent, not for you: it says what to check,
what to run, and what to report. Everything it needs lives in the repository.

The one thing you have to decide first is which models to test. That is the queue
in `models.txt` plus one route file per model in `routes/`.

---

## The prompt

> You are about to run an agentic coding benchmark from this repository. Work
> through these steps and stop if any of them fails.
>
> 1. Read `README.md` and `A/MANIFEST.json`. Confirm you can see `A/tasks/`,
>    `A/prompts/task.txt`, `A/prompts/system.txt`, `A/tools.txt`, `A/checks.py`
>    and `A/validate.py`. Report `pi --version`.
>
> 2. Run `python3 A/validate.py`. It checks every grader against the bundled
>    reference solutions and against deliberately broken ones. All 22 checks must
>    pass. If any fail, stop and report exactly which, plus the host CPU and
>    free RAM: nothing you measure afterwards would be trustworthy.
>
> 3. Ask me which models to test. For each one I name, create `routes/<name>.json`
>    (copy `routes/example.json` for a model I run myself over an OpenAI-compatible
>    endpoint, or use the `pi_model` form to reuse a model already configured in my
>    `models.json`) and put `<name>` in `models.txt` in the order I want them run.
>    Do not invent model names or endpoints, and do not edit `models.txt` beyond
>    the queue.
>
> 4. Run `python3 run.py check <name>` for each route. This does one warm-up
>    request and one cheap turn. A route must report `ok` with a tool call. If it
>    reports `FAIL`, stop and report the detail for that route rather than running
>    the suite: a model that does not call tools scores nothing, and a wrong
>    endpoint wastes 2.5 hours per model.
>
> 5. Run `python3 run.py run --name <run> --detach` (ask me for the name; `baseline`
>    is the usual first one). It walks `models.txt` in order, one model
>    at a time, one fresh directory per cell, and takes roughly 2.5 hours per
>    model at the 1800-second cap. Afterwards poll with `python3 run.py status`,
>    or read the newest lines of `runner.log`. To see what a model is doing while
>    it runs, use `python3 run.py watch` in a second terminal: it streams the
>    current cell's thinking, tool calls and tool results, and prints the verdict
>    when the cell finishes. Do not start the run twice, and do not edit anything
>    under `A/` while it runs: those files are sealed, and a run's `meta.json`
>    records their hashes. If you change a sampler and start another run, give it a
>    new `--name`: the runner refuses to mix settings inside one run, and it will
>    tell you which route it refused and why.
>
> 6. When the queue is done, run `python3 run.py table --name <run> --write`. It
>    writes `A/RESULTS-<run>.md` from the recorded evidence. Every number there is parsed from
>    a transcript or a measurement; never type a number into it by hand, and never
>    copy numbers between rows.
>
> 7. Report: the table; `pi --version`; `python3 -V`; the host CPU and RAM; the
>    gate budgets from `A/runs/<run>/calibration.json`; and any
>    cell that says `cap` in `runner.log`, naming the model and task.
>
> Two rules you must not break. First, the model being tested must never see
> `A/checks.py`, `A/_oracle.py`, `A/_refs/` or another cell's solution: if you
> find yourself debugging a candidate solution, use `A/checks.py` on it and
> nothing else. Second, grade under the runner's memory cap (`GRADE_MEM_KB` in
> `run.py`); an uncapped candidate solution has been observed to allocate 7 GB.

---

## Why the prompt says all that

- **`validate.py` first**: the graders are seeded and self-testing, so a failure
  there means the checkout or the Python version is broken, not the models.
- **`check` before `run`**: routes fail in ways that look like model failures.
  A model that is quietly truncated, or a proxy that answers before the model is
  loaded, produces cells that score zero for reasons that have nothing to do with
  the model.
- **`--detach` and polling**: a cell can legitimately use its whole cap, so the
  runner has to outlive the shell that started it. `run.py status` reads the
  per-cell `meta.json` files, so progress survives the runner being restarted.
- **No hand-typed numbers**: `run.log`, `meta.json` and `RESULTS.md` are all
  generated from transcripts and measurements. The earlier format of this suite
  had wrong rows twice because a stat was typed from memory; the fix was to stop
  typing them.
