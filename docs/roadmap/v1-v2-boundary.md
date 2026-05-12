# v1 / v2 boundary

A guide to what Inscript v1 includes and what it intentionally does
not. Every absence in v1 is a design decision, not a missing feature.

## How to read this document

The v1 interpreter is a **deliberately small artifact**: a
deterministic text interpreter for sequential rules and data
operations. The features listed under "v1 does not include" are not
on a TODO list — they are deferred for specific architectural
reasons. Each has a documented plan or open question in the
specification documents under `docs/spec/`.

If a feature is in v1, it has a locked specification, a working
implementation, and passing tests. If it is not in v1, the
interpreter does not pretend it exists: it produces a deterministic
error.

## What v1 includes

### Execution model

- **Sequential execution.** Statements run top to bottom, one line
  at a time. There is no listener loop, no event queue, no async.

### Vocabulary

- **7 verbs:** `remember`, `show`, `filter`, `count`, `gather`,
  `combine`, `each`.
- **29 reserved words total:** 7 verbs, 9 connectives, 4 operators,
  the multi-word component `equal`, 3 articles, 5 v2-reserved words.

### Data types

- **Numbers** — non-negative integers and decimals (`30`, `3.14`).
- **Single-token strings** — bare words that are neither numbers nor
  reserved words (`active`, `portland`). String values are
  case-folded to lowercase.
- **Homogeneous lists** — all numbers, all strings, or all records.
- **Records** — named-field bundles built with the `as` connective.
- **Named compositions** — reusable verb phrases stored under a
  user-defined name.

### Operations

- **In-place `filter`** — modifies the target list directly.
- **Non-destructive `combine`** — returns the sum without changing
  the source.
- **Auto-show** — `count`, `gather`, and `combine` display their
  results without an explicit `show`.
- **Copy semantics** — every data operation copies values. Two names
  never alias the same underlying collection.
- **Iterator context for `each`** — during iteration, names resolve
  first as a field on the current record, then against the symbol
  table. The binding is discarded when the loop ends.
- **Stepwise operation sequences** — when statements chain with
  `and` between complete verb phrases, each operation commits
  independently. A later failure does not roll back earlier side
  effects.

### Validation

- **Deterministic outcomes only** — every statement produces exactly
  one of: success, amber-precedence, amber-ambiguity, parse error,
  semantic error. No warnings, no silent fallbacks.
- **Canonical prose rendering** — the parser's interpretation of
  every successfully parsed statement is echoed back to the user
  before execution.

## What v1 does not include

Each item below is intentionally absent in v1 with a documented
reason.

### Authoring surfaces

- **Tile-composition interface.** The visual surface that lets a
  first-time user arrange vocabulary tiles into sentences. v1 is the
  text interpreter that the tile interface will eventually share an
  AST with. The tile surface is a separate engineering effort with
  its own design (slot-filtered tray, prose preview, validity
  indicator) and is not in scope here.
- **Proposal engine / authorize-don't-author authoring flow.** The
  design principle is that a new user should modify a working
  program rather than start from a blank file. The interpreter is
  the engine that runs whatever the proposal engine produces; the
  engine that proposes is a separate component.
- **Symbolic syntax surface.** A future terse form (e.g.
  `orders.filter(total > 50)`) over the same AST. Out of scope for
  v1.

### Vocabulary extensions

- **Domain packs.** Pluggable vocabulary modules (healthcare,
  business, home automation, legal/compliance, narrative) that add
  10–15 context-specific terms. Designed but not implemented.
- **`transform`, `choose`, `compare`.** Designed but with
  under-specified semantics: `transform` lacks a companion grammar
  (`by subtracting`, `by multiplying`); `choose` requires resolving
  more `or` context cases; `compare` has an undefined return value
  best paired with `choose`. All three are deferred to v2 with
  explicit grammars.
- **`when` and `unless`.** Temporal connectives for event-driven
  programs. Reserved in v1 but not executable — they require a
  listener model that is itself a v2 feature.

### Execution model

- **Event-driven execution.** No listeners, no reactivity. v1 only
  runs in a "do these things and stop" model. Healthcare protocols
  ("when blood pressure exceeds 180, alert the physician"), smart
  home triggers, and reactive game logic all require event-driven
  execution and are v2 use cases.
- **External data sources.** No databases, APIs, CSV imports, or
  file reads beyond the `.insc` source file itself. v1 data comes
  exclusively from `remember` and `gather`.
- **Scope isolation beyond the iterator context.** The symbol table
  is global. Compositions do not have their own local scope; they
  share the caller's symbol table. The iterator context is the only
  scoped binding in v1.

### Values and types

- **Multi-word strings / quoting.** A status value like
  `in progress` cannot be represented because `in` and `progress`
  would tokenize as separate words. A quoting mechanism is a v2
  consideration.
- **Negative numbers.** All numeric literals are zero or positive.
  Supporting negatives requires a minus-sign handling rule in the
  lexer.
- **Mixed-type lists.** A list cannot contain both numbers and text.
  Heterogeneous collections are a v2 type-system concern.

### Operations

- **Composition parameters.** A v1 composition is called by name
  alone — no arguments. `from` chaining between compositions is also
  deferred. Both require a parameter-passing model not yet designed.
- **Descending ranges.** `gather the numbers from 10 to 1` is a
  semantic error in v1. The reverse-iteration semantics are a v2
  feature.
- **Ranges over 10,000 items.** `gather` is capped to protect
  against runaway memory use. v1's target domains (business rules,
  compliance, data filtering at the hundreds-or-thousands scale)
  comfortably fit under the cap.
- **Reference / alias semantics.** All data operations copy. There
  is no way to have two names refer to the same underlying list.
  Immutable operations (as an alternative to in-place `filter`) are
  a v2 consideration.

## Why the line is here

The v1 boundary is drawn at the smallest interpreter that proves the
thesis. Specifically:

- The interpreter must show that **prose-as-syntax for general
  computation** can be deterministic — not a fuzzy natural-language
  layer.
- The 48 locked test sentences must execute exactly as the
  specification predicts, both for the 34 success cases and the 14
  hostile error cases.
- The pipeline must be reusable: the same AST and structured-result
  contract that the v1 text interpreter consumes will be consumed
  by the tile interface, the proposal engine, and (eventually) the
  event-driven runtime.

Anything beyond that risks coupling the next layer's design to early
implementation choices. Each deferred feature has a place in a later
build phase with its own specification and tests.

## Where to go next

- [`../language/quickstart.md`](../language/quickstart.md) — install
  and run the v1 interpreter.
- [`../language/syntax.md`](../language/syntax.md) — what you can
  write today.
- [`../architecture/pipeline.md`](../architecture/pipeline.md) — how
  the v1 interpreter is structured.
- [`../spec/inscript_addendum_v1d_build_boundary.md`](../spec/inscript_addendum_v1d_build_boundary.md)
  — the locked build-boundary specification that the v1 interpreter
  is built against.
