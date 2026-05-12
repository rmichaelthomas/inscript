# v1 → v2 boundary

A guide to what Inscript currently is and what it intentionally is not. Every absence is a design decision, not a missing feature.

## How to read this document

The Inscript interpreter is a **deliberately small artifact**: a deterministic text interpreter for sequential rules, data operations, and reusable filters. The features listed under "not yet built" are not on a TODO list — each has a documented reason and either a deferred-to-spec plan or an explicit closed-door decision. Each is referenced in a specification document under `docs/spec/`.

If a feature is shipped, it has a locked specification, a working implementation, and passing tests. If it is not yet shipped, the interpreter does not pretend it exists: it produces a deterministic error.

## Build state at a glance (May 12, 2026)

| Layer | Status | Spec |
|---|---|---|
| **v1 interpreter** | Shipped. 48 locked test sentences pass end-to-end. | Inception checkpoint + v1a/v1b/v1c/v1d |
| **v2a additions** | Shipped. `keep` verb, `of` connective (in `show`), multi-field `each show`, descriptor preservation, composition-chaining error wording. | v2a §67–§72 |
| **v1 UX polish** | Shipped. `--quiet` flag, named-offender error wording, auto-show truncation (`gather`/`keep` only). | — (code-only patches) |
| **v2.1-patches** | Shipped. Duplicate-field rejection in `each show`, `of`-on-list suggestion, list-operations-only error wording. | Locked retroactively in v2b §78–§80 |
| **v2b** | **Spec drafted. Not yet implemented.** Composition return values, generalize `of` to all value positions, list/iteration model clarification, U9 documentation note. | v2b §76–§81 |
| **v2** (event-driven) | Designed in scope, deferred. `when`/`unless`, listener model, `transform`/`choose`/`compare`. | Inception §13, §25 |
| **D7 — multi-word strings** | Explicitly deferred to its own checkpoint with external review. | v2a §72 |

## What is shipped

### Execution model

- **Sequential execution.** Statements run top to bottom, one line at a time. No listener loop, no event queue, no async.
- **Stepwise sequences.** When operations chain with `and` between complete verb phrases, each operation commits independently. A later failure does not roll back earlier side effects. (v1d §56)

### Vocabulary (31 reserved words)

- **8 verbs:** `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each`.
- **10 connectives:** `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`, `of`.
- **4 single-word operators:** `is`, `above`, `below`, `not`. Plus `equal` as a multi-word component (combines with `to` per inception §22).
- **3 articles:** `the`, `a`, `an`.
- **1 delimiter:** `:`.
- **5 v2-reserved (not executable in current build):** `when`, `unless`, `transform`, `choose`, `compare`.

### Data types

- **Numbers** — non-negative integers and decimals (`30`, `3.14`).
- **Single-token strings** — bare words that are neither numbers nor reserved words (`active`, `portland`). Case-folded to lowercase.
- **Homogeneous lists** — all numbers, all strings, or all records.
- **Records** — named-field bundles built with `as`.
- **Named compositions** — reusable verb phrases stored under a user-defined name.

### Operations

- **In-place `filter`** — modifies the target list directly.
- **Non-destructive `keep`** (v2a §67) — returns a fresh list of matches; source unchanged. Auto-shows by default; captures via `remember ... from keep ...`. Enables reusable filter compositions.
- **Non-destructive `combine`** — returns the sum without changing the source.
- **Single-record field access** (v2a §68) — `show <field> of <record>`. Currently scoped to `show`'s target position; v2b generalizes.
- **Multi-field `each show`** (v2a §69) — `each the docs show A and B` emits `A: ..., B: ...` per record. Single-field form unchanged.
- **Auto-show** — `count`, `combine`, `gather`, and `keep` (standalone) display their results without an explicit `show`.
- **Copy semantics** — every data operation copies values. Two names never alias the same underlying collection.
- **Iterator context for `each`** — during iteration, names resolve first as a field on the current record, then against the symbol table.
- **Composition reuse** — `keep`-based compositions are reusable across calls because the source is preserved (D3 dissolves under v2a §67).

### Display + validation

- **Deterministic outcomes only** — every statement produces exactly one of: success, amber-precedence, amber-ambiguity, parse error, semantic error. No warnings, no silent fallbacks. (v1c §50, §52)
- **Canonical prose rendering** — the parser's interpretation of every successfully parsed statement is echoed back to the user before execution. Suppressed with `--quiet`. (v1a §33)
- **Descriptor preservation** (v2a §71) — the user's descriptor (`a domain called X`) is preserved verbatim in canonical rendering rather than collapsed to `record`/`value`/`list`.
- **Named offenders in errors** — schema-mismatch errors call out the first record missing a field (with positional fallback when no source name is known). Zero-match vs. partial-match wording differs.
- **Auto-show truncation** — `gather`/`keep` auto-show output is truncated to first 10 + ellipsis + last 10 when the list exceeds 20 items. Explicit `show <list>` is never truncated.

### CLI

- **`--quiet`** — suppress the "I understand this as: ..." echo; mirror source blank lines so paragraph breaks survive.
- **`--test`** — auto-confirm amber prompts. Both flags work in any argument position; unknown `--flag` typos are rejected (not silently dropped).

## What is not yet built

Each item below is intentionally absent with a documented reason.

### Drafted but not yet implemented (v2b)

- **Composition return values.** A composition like `remember how to find-major: keep the docs where words is above 7000` does not yet flow into `remember the X called X from find-major` — the interpreter rejects `CompositionCallNode` in value position. The v2b §76 design (Path A: implicit return of the last operation's value, error at call site for void-result last ops) is locked but not wired through the interpreter. This is the next implementation chapter.
- **Generalized `of`.** Currently `of` only works after `show <field>`. The v2b §77 design extends `<field> of <record>` to any value position (e.g. `keep the docs where words is above words of doc-1`). Single-level only; chained `of` stays rejected until nested records exist.
- **List/iteration model clarification.** v2b §78 documents the v1/v2/v2b model: list operations only; per-record decisions belong in the where-clause. The v2.1-patch already ships the improved error wording for `each ... keep where ...`; the spec text lands in v2b.

### Authoring surfaces (still deferred)

- **Tile-composition interface.** The visual surface that lets a first-time user arrange vocabulary tiles into sentences. Will share the AST with the text interpreter.
- **Proposal engine / authorize-don't-author authoring flow.** First touch on a working program, not a blank file. The text interpreter is the engine; the proposal engine is a separate component.
- **Symbolic syntax surface.** A future terse form (e.g. `orders.filter(total > 50)`) over the same AST.

### Vocabulary extensions (still deferred)

- **Domain packs.** Pluggable vocabulary modules (healthcare, business, home automation, legal/compliance, narrative). Designed but not implemented.
- **`transform`, `choose`, `compare`.** Designed but under-specified — `transform` needs `by subtracting`/`by multiplying`; `choose` needs additional `or` cases; `compare`'s return is undefined. Deferred to v2 with explicit grammars.
- **`when` and `unless`.** Temporal connectives. Reserved but not executable — they require a listener model.

### Execution model (still deferred)

- **Event-driven execution.** No listeners, no reactivity. v1/v2b stays "do these things and stop." Healthcare protocols, smart home triggers, and reactive game logic are all event-driven v2 use cases.
- **External data sources.** No databases, APIs, CSV imports, or non-source file reads. Data comes from `remember` and `gather`.
- **Scope isolation beyond the iterator context.** The symbol table is global. Compositions share the caller's symbol table.

### Values and types

- **Multi-word strings / quoting (D7).** A status value like `in progress` cannot be represented because `in` and `progress` tokenize as separate words. v2a §72 defers D7 to a dedicated checkpoint with external review. Three candidate approaches catalogued (quoting, hyphenation convention, multi-word phrase spans); the hyphenation workaround (`in-progress`) remains valid in the meantime.
- **Negative numbers.** All numeric literals are zero or positive.
- **Mixed-type lists.** A list cannot contain both numbers and text.
- **Nested records.** Records are flat field→value maps. Chained `of` (`field-a of field-b of record`) is reserved until nested records exist.

### Operations (still deferred)

- **Composition parameters and chaining.** `<name> from <other>` for parameter passing remains v2-deferred (v1b §41 / Q9). v2b §76 unlocks `remember ... from <name>` (capture form) without unlocking parameter passing.
- **Per-record decision logic inside `each`.** `each ... keep where ...` is rejected with a list-level-suggestion error. v2b §78 closes the door on `each ... do <verb>` — if a future use case emerges that genuinely needs per-record reasoning beyond the where-clause, it returns as a fresh design item.
- **Descending ranges.** `gather the numbers from 10 to 1` is a semantic error.
- **Ranges over 10,000 items.** `gather` is capped.
- **Reference / alias semantics.** All data operations copy. Two names cannot share the same underlying list.

## Why the boundary moves the way it does

Each shipping round resolves specific gaps surfaced by dogfooding the previous one:

- **v1 → v2a:** the first dogfooding pass found that destructive `filter` made multi-pass analysis painful (D2), that there was no way to display multiple fields per record in `each` (D1), and no way to extract a single field of a single record (D4). v2a addressed all three with minimal vocabulary growth.
- **v2a → v2.1-patches:** the v2a dogfooding pass and the v1 UX polish round handled six small UX items without spec change.
- **v2a → v2b (drafted):** the second dogfooding pass found that `keep`-based compositions weren't usefully reusable because compositions don't return values (D9), and that `of` couldn't appear in `where` clauses or other value positions (D11). Both shape v2b.
- **v2b → next:** D7 (multi-word strings) gets its own checkpoint. v2-event-driven execution remains the largest deferred chapter.

The line moves only where dogfooding produces a sharply specified gap. The vocabulary budget is the clarity budget: every word added must pass the word salad test (inception §20) and every addendum locks the smallest spec change consistent with the surfaced gap.

## Where to go next

- [`../language/quickstart.md`](../language/quickstart.md) — install and run.
- [`../language/syntax.md`](../language/syntax.md) — what you can write today.
- [`../architecture/pipeline.md`](../architecture/pipeline.md) — how the interpreter is structured.
- [`../spec/`](../spec/) — the locked specification documents.
- [`../inscript_gap_inventory_2026_05_12_v1_dogfooding.md`](../inscript_gap_inventory_2026_05_12_v1_dogfooding.md) and [`../inscript_gap_inventory_2026_05_12_v2a_dogfooding.md`](../inscript_gap_inventory_2026_05_12_v2a_dogfooding.md) — the dogfooding inventories that drove the v2a and v2b spec work.
