# Quickstart

A short first-run guide for Inscript v1. If you want a deeper tour of
the language, read [`syntax.md`](syntax.md) next.

## Requirements

- Python 3.10 or later
- `pytest` (installed via the dev extras below)

## Install

```bash
git clone https://github.com/rmichaelthomas/inscript.git
cd inscript
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Run the test suite

There are 385 tests. They run in well under a second.

```bash
pytest tests/
```

A clean run is the easiest way to confirm the v1 interpreter is wired
up correctly in your environment.

## Run an example file

The repo ships with two example programs in `examples/`:

```bash
python -m inscript examples/program1_basics.insc
python -m inscript examples/program2_orders.insc
```

Each non-blank line is echoed first as canonical prose — the parser's
plain-English description of what it is about to run — followed by any
output the statement produces.

## Start the REPL

```bash
python -m inscript
```

You'll see:

```
Inscript v1 — type 'exit' to quit.
>
```

Type a statement and press enter. Type `exit` (or `quit`) to leave.

## Try this first

Save the following three lines as `demo.insc`:

```
gather the numbers from 1 to 10
filter the numbers where each is above 5
combine the numbers
```

Run it:

```bash
python -m inscript demo.insc
```

Expected output (the `I understand this as:` lines are the canonical
preview):

```
I understand this as: gather the numbers from 1 to 10
1, 2, 3, 4, 5, 6, 7, 8, 9, 10
I understand this as: filter the numbers where each is above 5
I understand this as: combine the numbers
40
```

What happened:

- `gather` built `[1, 2, ..., 10]`, stored it under the name `numbers`,
  and auto-shows it.
- `filter` modified `numbers` in place. After this line `numbers` holds
  `[6, 7, 8, 9, 10]`. There is no output because `filter` is silent on
  success.
- `combine` summed the remaining numbers (6 + 7 + 8 + 9 + 10 = 40) and
  auto-shows the result. The source list is unchanged — `combine` does
  not modify `numbers`.

## Test mode

If you want to run a `.insc` file non-interactively without being
prompted to confirm amber outcomes (such as a mixed-precedence
condition), use `--test`:

```bash
python -m inscript --test examples/program2_orders.insc
```

## Where to go next

- [`syntax.md`](syntax.md) — full v1 syntax tour.
- [`../architecture/pipeline.md`](../architecture/pipeline.md) — how a
  source line becomes a result.
- [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) — what
  v1 includes and what it deliberately does not.
- [`../spec/`](../spec/) — the immutable specification documents the
  v1 interpreter is built against.
