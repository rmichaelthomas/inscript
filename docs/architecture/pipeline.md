# Pipeline architecture

A guide to how Inscript turns a source line into a result. This
document walks the stages in plain English. The pipeline shape
established in v1 (lexer → reorderer → parser → analyzer →
interpreter, with the canonical renderer and structured-result handling
around them) is unchanged through v2a and the v2.1-patches — every
extension since v1 adds rules to existing modules without adding
stages or moving the I/O boundary. For module-level implementation
details, read the source under `src/inscript/`. For the authoritative
behavior, read `docs/spec/`.

## The path of a line

```
source line
   │
   ▼
┌─────────────┐
│   lexer     │  tokens
└─────────────┘
   │
   ▼
┌─────────────┐
│  reorderer  │  canonical-order tokens
└─────────────┘
   │
   ▼
┌─────────────┐       ┌────────────────────┐
│   parser    │──────▶│ canonical renderer │  echoes "I understand this as: ..."
└─────────────┘       └────────────────────┘
   │
   ▼
┌──────────────────┐
│ semantic analyzer│
└──────────────────┘
   │
   ▼
┌─────────────┐
│ interpreter │
└─────────────┘
   │
   ▼
┌─────────────────────┐
│  structured result  │  (one of five outcomes)
└─────────────────────┘
   │
   ▼
┌────────────┐
│   CLI      │  prints the canonical preview, output, or error
└────────────┘
```

Each stage either passes work forward or short-circuits with a
structured result. No stage prints or reads — only the CLI does
that.

## Stage by stage

### Lexer

Turns a single source line into a list of typed tokens. The lexer is
the most mechanical stage:

- Lowercases everything.
- Strips decorative punctuation (commas, periods, question marks,
  exclamation marks) from the edges of words.
- Splits on whitespace, keeping hyphenated names like
  `find-big-orders` together.
- Recognizes the colon `:` as its own token (used in composition
  definitions).
- Combines `equal` followed by `to` into a single operator token
  `equal_to`.
- Identifies blank lines (and lines that are only punctuation) as
  producing zero tokens, which the rest of the pipeline skips.

Each token carries a category: verb, connective, operator, article,
delimiter, number, or unknown. "Unknown" simply means "not in the
reserved vocabulary" — that is where user-provided names and string
values live.

### Reorderer

Inscript expects canonical word order (`verb the target ...`). The
reorderer accepts a narrow set of natural variations and rejects
everything else with a suggestion. In particular it accepts:

- Canonical order: `filter the orders where total is above 50`.
- Target before verb with an article: `the orders filter where total
  is above 50` → reordered to canonical.
- Target before verb without an article: `orders filter where total
  is above 50` → reordered to canonical.

Anything else (verb at the end, scrambled condition elements, etc.)
produces a parse error with a canonical-form suggestion. The wider
free-order acceptance is reserved for the future tile-composition
interface; the v1 text interpreter keeps the acceptance band narrow
on purpose.

If the input has no recognizable verb at all, the reorderer passes
the tokens through so the parser can try the named-composition
fallback.

### Parser

Builds an abstract syntax tree (AST). The parser is **slot-filling**:
each verb has a known signature (e.g. `filter` expects a target and a
condition), and the parser walks the tokens filling each slot in
canonical order. The eight verbs (`remember`, `show`, `filter`,
`keep`, `count`, `gather`, `combine`, `each`) each route to a
verb-specific sub-parser that shares helpers — `keep` and `filter`
share their target-plus-condition shape, for instance.

Several words in the language change meaning depending on context.
The parser resolves all of them deterministically with parser state
plus one-token lookahead:

- `and` / `or` — list construction, compound condition, operation
  sequencing, record-field continuation, or multi-field display
  inside `each ... show` (five contexts), depending on which clause
  is active and what the next token is.
- `is` — comparison introducer (followed by an operator) or equality
  operator (followed by a value).
- `not` — always modifies the operator that follows.
- `to` — range endpoint after `from <number>`, or part of `equal to`.
- `from` — range start in `gather`, result capture in `remember`
  (next token is a verb), or simple reference (next token is a name).
- `each` — iteration verb in verb position; pronoun for the current
  item inside a `where` clause.
- `of` — field-access connective in `show <field> of <record>`.

If a `where` clause mixes both `and` and `or`, the parse still
succeeds (standard precedence: `and` binds tighter than `or`), but
the parser flags an amber-precedence outcome so the user can confirm
the grouping before execution.

If parsing fails, the parser returns a parse error with a plain-
English message — never an "unexpected token at column N" style
error.

### Canonical renderer

The renderer is the inverse of the parser. It walks the AST and
produces a canonical English sentence representing exactly what the
interpreter is about to run.

This sentence is what the CLI prints right before each statement
executes (unless you pass `--quiet`, which suppresses the echo while
keeping data output):

```
I understand this as: filter the orders where total is above 50
```

The renderer preserves your descriptor verbatim, so the prose you
wrote reads back the same way:

```
I understand this as: remember a domain called mobius with docs as 91 and words as 381476
```

(The interpreter ignores `domain` for semantics — descriptors are
decorative — but the canonical-prose echo keeps your wording.)

The renderer also produces a parenthesized variant for amber-
precedence messages so the user sees the parser's grouping in plain
form.

The canonical rendering is more than cosmetic — it round-trips. A
canonical sentence, fed back into the parser, produces the same AST.
That property is exercised by the test suite for every example in the
spec.

### Semantic analyzer

The analyzer takes the AST and the current symbol table and checks
that the operation makes sense before any execution happens. Among
the things it verifies:

- The names referenced actually exist in the symbol table.
- The operation matches the target's type: `filter`, `count`, and
  `each` need a list; `combine` needs a list of numbers.
- For field operations on a list of records, every record in the list
  actually has the referenced field.
- A list under construction has only one kind of item — numbers,
  text, or records — never a mix.
- A `gather` range is ascending and contains at most 10,000 items.
- Named compositions are checked for grammar at definition time and
  for name resolution at call time, so a composition can reference
  data that does not yet exist when defined.

Each failure becomes a semantic-error result with a clear message.
Nothing executes if the analyzer is unhappy.

### Interpreter

The interpreter runs the validated AST against a mutable symbol
table. Key behaviors:

- **`remember` mutates the symbol table.** A new entry is created, or
  an existing one is silently overwritten. The type can change.
- **`filter` modifies the target list in place.** The original list
  loses items that did not match. There is no output on success.
- **`keep` returns a fresh list.** Like `filter` but non-destructive
  — the source is untouched. `keep` auto-shows its matches by
  default, or its result can be captured via `remember ... from keep
  ...`. This is the reuse primitive: a `keep`-based composition is
  callable repeatedly with the same input.
- **`count`, `gather`, and `combine` auto-show.** `gather` also
  stores its result under the parsed name. `keep` also auto-shows.
- **`combine` is non-destructive.** It returns a sum without changing
  the source list.
- **`each` runs the action once per item.** Inside the action, names
  resolve first against the current item (as a field on a record)
  and then against the symbol table. The sub-action can be `show
  <field>` or `show <field> and <field>` for multi-field display.
- **Copy semantics everywhere.** Data is copied when stored or
  retrieved by name. Two names never alias the same underlying
  collection.
- **Stepwise execution.** When several operations are joined by `and`
  (sequencing, not condition), each one commits independently. If a
  later one fails, earlier side effects remain and the error message
  names what was completed (with proper capitalization).

### Structured result

Every statement produces exactly one of five outcomes:

| Outcome             | Meaning                                              |
|---------------------|------------------------------------------------------|
| `success`           | Parse, analysis, and execution all succeeded.        |
| `amber_precedence`  | A `where` clause mixes `and` and `or`. Awaiting user confirmation. |
| `amber_ambiguity`   | The reorderer cannot uniquely resolve slot filling. Awaiting clarification. |
| `error_parse`       | The AST could not be built.                          |
| `error_semantic`    | The AST built, but execution would not make sense.   |

The result carries the canonical prose form, any output lines, an
explanation message for non-success outcomes, and a flag indicating
whether execution actually occurred.

This is the full result vocabulary. There is no "warning" category,
no silent fallback, no probabilistic outcome. The interpreter is
deterministic: the prose either runs as written or it does not run
at all.

### CLI display

The CLI wrapper (`src/inscript/cli.py`) is the only module that calls
`input()` or `print()`. It receives the structured result and renders
it for the terminal:

- For success it prints the canonical preview line, then any output
  lines. The preview is suppressed under `--quiet`.
- For amber outcomes it prints the message and prompts for
  confirmation (or auto-confirms in `--test` mode). On confirmation
  the canonical preview is not re-emitted before execution.
- For errors it prints the message prefixed with `Error:`.

The CLI also applies two display refinements:

- **Auto-show truncation.** When `gather` or `keep` auto-shows a list
  longer than 20 items, the display is condensed to the first 10
  items, an ellipsis, and the last 10 items. The symbol table holds
  the full list; only the display is shortened. Explicit `show
  <list>` is never truncated — you asked for the whole list.
- **Blank-line preservation in `--quiet`.** Blank lines in the source
  file mirror to the output so paragraph breaks survive.

Flags can appear in any argument position, and unknown `--flag`
typos error rather than silently falling through.

If you embed the interpreter in another program, you bypass the CLI
and inspect the structured result directly. Every behavior the CLI
shows the user is available as plain data.

## Why this shape

Each stage exists because it solves one specific problem the
preceding stage cannot:

- A free-form text source needs **tokenization** before any structure
  can emerge.
- A bounded but human-friendly word order needs a **reorderer** to
  bridge typed prose to a canonical grammar.
- A grammar with seven context-dependent words needs a **parser**
  with state and lookahead.
- A user-facing language needs a **canonical renderer** so the user
  can always see what the parser understood.
- A typed data model with field-based filtering needs a **semantic
  analyzer** to catch problems before execution.
- An interpreter that prints to a terminal in one deployment, runs in
  a tile interface in another, and is embedded in tests in a third
  needs to **return data**, not perform I/O.

Five stages, one boundary for I/O, five possible outcomes per
statement. Nothing more.

## Where to go next

- [`../language/quickstart.md`](../language/quickstart.md) — install
  and run the interpreter.
- [`../language/syntax.md`](../language/syntax.md) — the full v1
  syntax.
- [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) —
  what v1 includes and what is intentionally deferred.
- `src/inscript/` — the module-by-module implementation.
- [`../spec/`](../spec/) — the locked specification documents.
