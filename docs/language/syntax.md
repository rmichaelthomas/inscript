# Inscript syntax

A practical guide to writing Inscript programs. Inscript is a bounded
prose language: 31 reserved words plus user-provided names and literal
values. The prose IS the program.

This guide covers v1 plus the v2a additions that have shipped: the
`keep` verb, the `of` connective, multi-field `each show`, and
descriptor preservation. See
[`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) for
what's drafted in v2b but not yet implemented.

If you have not run the interpreter yet, start with
[`quickstart.md`](quickstart.md).

## Source files

- An Inscript source file uses the `.insc` extension and is plain
  text.
- **One statement per line.** Each non-blank line is a complete
  statement.
- **Blank lines are skipped.** Use them freely as paragraph breaks
  between groups of statements.
- **Decorative punctuation is stripped.** Commas, periods, question
  marks, and exclamation marks at word edges are removed before
  parsing, so you can punctuate naturally:
  `show colors.` is read as `show colors`, and
  `filter the orders where total is above 50.` is read as
  `filter the orders where total is above 50`.
  Commas are decorative only; they do not replace `and` as a list
  separator. In v1, list items are always joined by `and`.
- **Case-insensitive.** `SHOW Age` and `show age` are identical to the
  interpreter. Names and string values are normalized to lowercase
  internally.

## Names

User-provided names (variables, fields, named compositions) follow
three rules:

- Start with a letter.
- Contain letters, digits, and hyphens.
- Cannot be one of the 31 reserved words.

Valid: `age`, `orders`, `find-big-orders`, `order1`, `my-list`.

Invalid: `1st-order` (starts with a digit), `filter`
(reserved verb), `when` (reserved for v2).

## Verbs

There are eight verbs. Most statements begin with one.

### `remember`

Stores a value, list, record, or named composition.

**A single value:**

```
remember a number called age with 30
remember a value called greeting with hello
```

The descriptor between the article and `called` (here `number` and
`value`) is decorative — the interpreter ignores it for semantics. The
type is inferred from the value itself: `30` is a number, `hello` is
text. Your descriptor is preserved in the canonical-prose echo
("I understand this as: remember a number called age with 30") so the
language reads back the way you wrote it.

**A list:**

```
remember a list called colors with red and blue and green
remember a list called nums with 1 and 2 and 3 and 4 and 5
```

Items are separated by `and`. Lists must be homogeneous — see
[Lists](#lists).

**A record (with fields):**

```
remember an order called order1 with total as 75 and status as active
```

Use `as` to assign a value to each named field. Fields are separated
by `and`.

**Capturing a verb-phrase result:**

```
remember the result called total from combine the numbers
```

When you use `from <verb-phrase>` instead of `with <value>`, the
interpreter executes the inner phrase and stores its return value.

**A named composition:**

See [Named compositions](#named-compositions) below.

If you `remember` something with a name that already exists, the new
value silently overwrites the old one. The type can change.

### `show`

Displays a value.

```
show age
show colors
```

A list of strings or numbers shows as comma-separated values
(`red, blue, green`). A record shows as `field: value` pairs. A list
of records shows one record per line.

Inside `each`, `show` may be used without a target to display the
current iterator item.

**Single-record field access** uses `of`:

```
show total of order1
show status of order1
```

`<field> of <record>` extracts one field from a named record. The
field must exist on that record, and `<record>` must be a single
record (not a list — for lists, iterate with `each`). See the
[`of` connective](#the-of-connective) section.

### `filter`

Reduces a list **in place** by a condition.

```
filter the orders where total is above 50
filter the orders where status is active
filter the numbers where each is above 5
```

After `filter`, the original list contains only the items that
matched. Filter produces no output on success — use `show` or `count`
afterward to inspect the result. To filter without mutating the
source, use [`keep`](#keep) instead.

### `keep`

Like `filter`, but **non-destructive**: returns the matching items as
a fresh list while leaving the source untouched.

```
keep the orders where total is above 50
```

By default, `keep` auto-shows its matches. To capture the result for
further analysis, use `remember ... from keep ...`:

```
remember the big-orders called big from keep the orders where total is above 50
show big
count the orders   # still 3 — keep didn't mutate the source
```

`keep` is the natural building block for reusable filter compositions:

```
remember how to find-big: keep the orders where total is above 50
find-big   # auto-shows matches; orders unchanged
find-big   # callable again; same result
```

(Capturing `find-big`'s result via `remember the X from find-big`
needs composition return values — drafted in v2b but not yet
implemented. Until then, use the inline form `remember the X from keep
the orders where ...`.)

**Conditions** have the shape `<field> is <operator> <value>` or, for
flat lists, `each is <operator> <value>`:

| Operator        | Meaning                                          |
|-----------------|--------------------------------------------------|
| `is`            | equality (when not followed by another operator) |
| `is above`      | strictly greater than                            |
| `is below`      | strictly less than                               |
| `is equal to`   | explicit equality                                |
| `is not above`  | less than or equal to (includes the boundary)    |
| `is not below`  | greater than or equal to (includes the boundary) |
| `is not equal to` | not equal                                      |

Note that `not above N` means `≤ N` — the boundary value `N` is
*kept*, not removed. This is intentional and distinct from `below N`.

**Compound conditions** use `and` and `or` inside the same `where`:

```
filter the orders where total is above 50 and status is active
filter the orders where total is below 30 or status is pending
```

`and` binds tighter than `or`. Mixing them in a single condition
triggers a confirmation prompt before execution.

### `count`

Returns the number of items in a list, and shows the result.

```
count the colors
count the orders
```

### `gather`

Generates an inclusive numeric range, stores it, and shows it.

```
gather the numbers from 1 to 10
```

The name after the article (`numbers`) becomes the new symbol. v1
ranges must be ascending (`from` ≤ `to`) and contain at most 10,000
items.

### `combine`

Sums the numbers in a list. The result is shown.

```
combine the numbers
```

`combine` does **not** modify the source list. To capture the sum, use
`remember ... from combine ...`:

```
remember the result called total from combine the numbers
```

`combine` is numeric-only in v1: it cannot concatenate strings or
merge records.

### `each`

Iterates over a list. For every item the sub-operation runs once
against that item.

```
each the orders show total
each the orders show status
each the numbers show
```

While inside `each`, the iterator binds a "current item" used for two
purposes:

- A field name in the sub-operation resolves against the current
  record. `show total` looks up `total` on each order.
- `show` with no argument displays the current item itself — useful
  for flat lists or whole records.

**Multi-field display.** Inside `each ... show`, multiple field names
can be separated with `and` to produce one labeled line per record:

```
each the orders show total and status
```

Output:

```
total: 75, status: active
total: 30, status: active
total: 120, status: pending
```

Field order in the output follows the user's order in the source.
Three or more fields work the same way (`show a and b and c`).
Listing the same field twice (`show class and class`) is a semantic
error — the language assumes that's a typo.

Inside a `where` clause, `each` is a **pronoun** for the current item
being tested, not the iteration verb:

```
filter the numbers where each is above 5
```

**Note:** `each ... keep where ...` is rejected at parse time. `keep`
and `filter` are list operations; per-record decisions live in the
where-clause of a list operation, not in an `each` body. The error
suggests the list-level alternative.

## Lists

Lists are constructed with `and` between values:

```
remember a list called colors with red and blue and green
remember a list called scores with 1 and 2 and 3
remember a list called orders with order1 and order2 and order3
```

In v1, **lists are homogeneous**. Every item must be the same kind:
all numbers, all text, or all records. Mixing types is a semantic
error:

```
remember a list called bad with 1 and blue
```

> Error: A list can't mix numbers and text. '1' is a number but 'blue'
> is text.

If you write `remember a list called X with Y` (a single item), the
descriptor `list` forces list construction so `X` is a one-item list,
not a flat value.

## Records

Records use `as` to bind values to named fields:

```
remember an order called order1 with total as 75 and status as active
remember an order called order2 with total as 30 and status as active
```

Inside a list of records, every record should share the same field
names. When you reference a field in a `where` clause (such as
`total`), the interpreter checks that every record in the list has
that field — otherwise it stops before running, and the error names
the first record that's missing the field:

> Error: 'item1' in 'mixed-records' doesn't have a field called
> 'total'. Other items do have it.

When no record at all has the field, the wording reflects that:

> Error: No item in 'orders' has a field called 'nonexistent'.

## The `of` connective

`<field> of <record>` accesses one field of one record. It's the
counterpart to `each ... show <field>` for cases where you just want
one value from one named record:

```
show total of order1
show status of order1
```

Three checks fire at parse/validation time:

- The record name must exist (`'ghost' is unknown` → error).
- It must be a single record, not a list. If you point `of` at a list,
  the error suggests `each`:

  > Error: 'of' needs a single record. 'orders' is a list of records
  > — did you mean: each the orders show total?

- The record must have the named field.

In the current build, `of` only works in `show`'s target position.
Generalizing it to value positions (e.g. `keep the docs where total
is above total of baseline`) is drafted in v2b but not yet
implemented.

## Named compositions

Use `remember how to <name>: <body>` to define a reusable sentence.
The body is parsed at definition time but its names are resolved at
call time.

```
remember how to find-big-orders: filter the orders where total is above 50
```

Call the composition by writing its name on its own line:

```
find-big-orders
```

A composition body may chain operations with `and`:

```
remember how to count-active: filter the orders where status is active and count the orders
```

Calling a composition runs its body against the current symbol table.
If the body references a name that does not exist when you call it,
the interpreter raises a semantic error at the call site, not at the
definition.

The current build does not support passing arguments to compositions,
and the composition name must stand alone — no `from` chaining yet.
Attempting `find-big-orders from orders` produces:

> Error: Composition chaining isn't supported yet. Call
> 'find-big-orders' on its own line.

Capturing a composition's return value (`remember the X from
find-big-orders`) is drafted in v2b but not yet implemented. Until
then, use the inline form: `remember the X from keep the orders where
...`.

## Values

A literal value can be:

- **A number** — digits with an optional single decimal point.
  Examples: `30`, `3.14`, `100`. v1 does not support negative numbers
  or scientific notation.
- **A single-word string** — any bare word that is not a number and
  not in the reserved-word list. Examples: `red`, `active`,
  `portland`. Strings are case-folded to lowercase.

The language does **not** support multi-word strings. A status value
like `in progress` cannot be expressed because `in` and `progress`
would tokenize as separate words. A quoting mechanism is the open D7
question — see [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md).
The hyphenation workaround (`in-progress`) is the recommended pattern
in the meantime.

Vocabulary words (the 31 reserved words) cannot be used as values
either:

```
remember a list called items with filter and blue
```

> Error: The word 'filter' is a verb in Inscript and can't be used as
> a value. Try a different word.

## Mixed `and` / `or` and the amber prompt

A `where` clause that mixes `and` and `or` is unambiguous to the
parser (standard precedence: `and` binds tighter than `or`) but
ambiguous to human intuition. The interpreter pauses and shows you
the grouping it's about to use:

```
filter the orders where total is above 50 and status is active or status is pending
```

> I'll read this as: (total is above 50 and status is active) or
> status is pending. Is that what you mean? If not, split it into two
> statements.

Type `y` to proceed or `n` to abort and rewrite. Single-operator
chains (`A and B and C`, or `A or B or C`) do not trigger the prompt
because associativity makes the parse unambiguous to read.

## Limitations at a glance

- **Single-word strings only.** No quoting yet (D7, deferred).
- **Homogeneous lists only.** All numbers, all text, or all records.
- **No negative numbers.** All literals are zero or positive.
- **Range cap.** `gather` produces at most 10,000 items.
- **Ascending ranges only.** `from` must be less than or equal to `to`.
- **No event-driven execution.** `when` and `unless` are reserved but
  not executable.
- **No `transform`, `choose`, `compare`.** Reserved for v2.
- **No composition return capture yet.** `remember the X from
  <composition>` is drafted in v2b but not implemented; use the
  inline form (`remember the X from keep the orders where ...`)
  meanwhile.
- **`of` only in `show`'s target position.** Generalizing to all
  value positions is drafted in v2b.
- **Single-level `of` only.** `field-a of field-b of record` is a
  parse error; nested records don't exist yet.
- **List operations only.** `keep`/`filter` operate on lists.
  `each ... keep where ...` is rejected (the error suggests the
  list-level alternative).

See [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) for
the full boundary.

## Where to go next

- [`../architecture/pipeline.md`](../architecture/pipeline.md) — how
  the interpreter turns a source line into output.
- [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) — the
  intentional boundaries of v1.
- [`../spec/`](../spec/) — the locked specification documents, if you
  want the authoritative source.
