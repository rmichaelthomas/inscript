# ADDENDUM
## Inscript Programming Language — Composition Parameters and Conditional Branching
### v2d — The Input Side and the Last Control Flow

**Status:** LOCKED — EXTENDS `inscript_addendum_v2c_multi_word_strings.md`
**Date:** May 12, 2026
**Author:** Rob Thomas / R. Michael Thomas
**Document type:** Addendum — resolves Q9 (composition parameters) by adding named parameter declaration and passing via `from`, and promotes `choose` from deferred to active with `if`/`otherwise` connectives for conditional branching. Continues deferral of `transform` and `compare`.
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Extends `inscript_addendum_v2c_multi_word_strings.md` (May 12, 2026), which extends v2b/v2a/v1d/v1c/v1b/v1a and the Inception Checkpoint v1 (May 11, 2026). Continues from §95. Resolves Q9 (composition parameters), which was partially resolved by v2b §76 (return values) — this addendum completes it with the input side. Promotes `choose` from the v2 deferred verb table (inception §21, v1a §29) to active verb with full grammar specification.

---

## HOW TO READ THIS DOCUMENT

- §96 locks **composition parameters** — named parameter declared with `from` in the definition, passed with `from` at the call site. Single parameter, local scope, copy semantics, names-only.
- §97 locks **parameter mismatch errors** — calling with/without a parameter when the composition does/doesn't expect one.
- §98 locks **parameterized calls in value-capture position** — `remember the r called r from comp from name` works via peek-ahead disambiguation.
- §99 locks **`choose` verb** — `choose if <condition>: <action> otherwise <action>`. Two new connectives: `if`, `otherwise`.
- §100 locks **`choose` condition syntax** — value expressions with existing operators, no new condition machinery.
- §101 locks **multi-way branching and multi-statement actions** — `otherwise if` chaining, `and` sequencing inside branches, colon as context switch.
- §102 locks **`choose` as side-effect only** — added to the v2b §76 list. `choose` inside `each` deferred.
- §103 locks **continued deferral of `transform` and `compare`**.
- §104 updates the vocabulary table. **Two new reserved words** (`if`, `otherwise`). `choose` moves to active. 31 → 33.
- §105 adds test sentences 81–95 to the test suite (extending from v2c §94's sentence 80).
- §106 extends the build boundary (v2c §95).

---

### §96 — COMPOSITION PARAMETERS: NAMED PARAMETER WITH `from`

**Decision: Compositions accept a single named parameter declared with `from` between the composition name and the colon in the definition. The parameter is passed with `from` at the call site. The parameter creates a local binding — it shadows any global name for the duration of the call, and the global scope is restored after the call returns. The parameter receives a copy of the passed value. Only names (not value expressions) may be passed as parameter values. LOCKED as composition parameter semantics. Resolves Q9 (composition parameters) fully — v2b §76 resolved the output side (return values), this section resolves the input side.**

**Definition syntax:**

```
remember how to find-big from data: keep the data where total is above 50
```

The `from data` between the composition name (`find-big`) and the colon declares a parameter named `data`. The body uses `data` as a regular name reference. The parameter name follows the same rules as all names: letters, digits, and hyphens, starting with a letter, lowercased by the lexer (inception §22, v1d §57). The parameter name is subject to reserved-word exclusion (v1a §29) — `from filter` in a definition is an error.

**Call syntax (standalone):**

```
find-big from orders
```

The `from orders` passes the value of `orders` as the parameter. The interpreter looks up `orders` in the symbol table, deep-copies its value (inception §24 copy semantics), binds the copy to `data` in a local scope, and executes the body. After execution, the local binding is removed and any shadowed global name is restored.

**Call syntax (value capture):** See §98.

**Scope mechanics.** The interpreter implements a save/bind/execute/restore pattern:

1. If the parameter name already exists in the symbol table, save the existing entry.
2. Bind the parameter name to a deep copy of the passed value.
3. Execute the composition body.
4. Remove the parameter binding.
5. If an entry was saved in step 1, restore it.

This is a scope stack of depth 1 — no general-purpose scope chain is needed. Only the parameter is local. Everything else the body does (`remember` creating new names, `filter` modifying lists, auto-show output) writes to the global scope, consistent with existing composition behavior. A composition call is semantically equivalent to pasting the body's statements at the call site with the parameter bound — the same mental model users already have.

**Why single parameter:** multiple parameters would require grammar for separation (another `and` meaning? a new connective?), ordering rules, and disambiguation with existing `and` contexts. None of the v1/v2 target domains need multi-parameter compositions — the dominant pattern is "apply this reusable operation to this data." The single-parameter shape handles that. If multi-parameter need surfaces from dogfooding, it can be designed with a concrete use case. The language's track record confirms: features designed from observed need land cleanly.

**Why names-only:** allowing value expressions as parameters (`find-big from keep the tasks where ...`) would create multi-`from` parsing complexity and long lines that fail the word salad test. The user writes two clear lines instead:

```
remember the active called active from keep the tasks where status is active
find-big from active
```

The existing `remember ... from <verb-phrase>` capture mechanism handles the first line; composition parameters handle the second. Each line does one thing.

**`from` disambiguation update.** Extending the table in v1b §43 / v1b §44:

| Context | `from` meaning | Disambiguation |
|---|---|---|
| Inside `gather` | Range start: `gather the nums from 1 to 10` | Parser state = inside `gather` clause |
| After `remember ... called <name>` + next is VERB | Value capture from verb phrase | Next token is VERB |
| After `remember ... called <name>` + next is UNKNOWN | Value capture from name or parameterized composition call (§98) | Next token is UNKNOWN; peek further — see §98 |
| After `how to <name>` | Parameter declaration | Parser state = inside composition definition, before colon |
| After UNKNOWN as standalone statement | Parameter passing | Parser state = top-level or inside composition body; token is UNKNOWN followed by `from` |

Each entry is unambiguous given parser state and one-token lookahead (v1c §51). No existing `from` meaning changes.

---

### §97 — PARAMETER MISMATCH ERRORS

**Decision: Calling a composition that expects a parameter without one, or calling a composition that doesn't expect a parameter with one, produces a semantic error at the call site. LOCKED as parameter enforcement.**

**Case 1 — Expected parameter, none provided:**

```
remember how to find-big from data: keep the data where total is above 50
find-big
```

→ Outcome 5: *"'find-big' expects an input (from <data>). Try: find-big from <your-list>."*

The error fires at the call site before the body executes. The body references `data`, which would fail with a generic missing-name error — but the parameter-mismatch error is more informative because it explains *why* the name is missing and shows the expected syntax.

**Case 2 — No parameter expected, one provided:**

```
remember how to show-all: show orders
show-all from tasks
```

→ Outcome 5: *"'show-all' doesn't take an input. Call it on its own: show-all."*

The error fires at the call site. The alternative — silently ignoring the `from tasks` — would violate deterministic interpretation (v1c §52). The user thinks they're passing data; silently dropping it means the program does something different from what they wrote.

Both errors are Outcome 5 (semantic error, v1c §50) — the program is grammatically valid but semantically wrong. Consistent with v2b §76's call-site error pattern for void-result compositions.

---

### §98 — PARAMETERIZED CALLS IN VALUE-CAPTURE POSITION

**Decision: `remember the r called r from find-big from orders` works. The parser handles the two `from` tokens by peek-ahead: after consuming `find-big` in value-capture position, the parser peeks for `from` and, if found, parses `find-big from orders` as a parameterized composition call whose return value is captured. LOCKED as value-capture disambiguation extension.**

The line `remember the r called r from find-big from orders` contains two `from` tokens:

1. The first `from` (after `called r`) means value capture (v1b §43 meaning 2/3).
2. The second `from` (after `find-big`) means parameter passing (§96).

The parser is in value-capture mode after `remember the r called r from`. It sees `find-big` (UNKNOWN). It peeks ahead: the next token is `from` (CONNECTIVE). Since parameters are names-only (§96), `from UNKNOWN` after a potential composition name is always a parameterized call. The parser consumes `find-big from orders` as a single value expression — a parameterized composition call — and the outer `remember ... from` captures its return value.

**Disambiguation rule (extending v1b §43 meanings 2/3):** When the parser is in value-capture mode and sees UNKNOWN as the potential value source:
- Peek ahead: if next token is `from`, parse `UNKNOWN from UNKNOWN` as a parameterized composition call.
- Otherwise: parse UNKNOWN as a plain name reference (existing behavior).

Name resolution happens at call time (inception §23). If `find-big` turns out not to be a composition, the interpreter produces the existing missing-composition error.

**Three-deep nesting is not supported.** `remember the r called r from comp-a from comp-b from orders` would require value-expression parameters (passing a composition call as a parameter), which §96 decided against. The user writes two lines:

```
remember the inner called inner from comp-b from orders
remember the r called r from comp-a from inner
```

---

### §99 — `choose` VERB: CONDITIONAL BRANCHING

**Decision: `choose` is promoted from the v2 deferred verb table to active verb. The grammar is `choose if <condition>: <consequence> [otherwise <alternative>]`. Two new connectives are added: `if` (introduces the condition) and `otherwise` (introduces the alternative). LOCKED as `choose` verb specification.**

The inception checkpoint (§21) deferred `choose` with signature `condition + consequence + alternative` but did not specify the grammar. This section locks it.

**Grammar:**

```
choose if <condition>: <action> otherwise <action>
```

- `choose` — the verb. Signals a decision.
- `if` — new connective (CONNECTIVE token). Introduces the condition.
- `<condition>` — a boolean expression using existing operators (§100).
- `:` — the colon delimiter (inception §22). Separates condition from consequence. Consistent with its role in composition definitions.
- `<action>` — one or more operations (§101).
- `otherwise` — new connective (CONNECTIVE token). Introduces the alternative. Optional — if omitted and the condition is false, nothing happens.

**Word salad test (§20):** A non-programmer reads `choose if total of order1 is above 50: show "big" otherwise show "small"` and understands it instantly. `if` and `otherwise` are the most natural English words for conditional branching. No explanation needed.

**Verb signature** (extending inception §17):

| Verb | Slots |
|---|---|
| `choose` | condition (after `if`, before `:`), consequence (after `:`), alternative (after `otherwise`, optional) |

**The `otherwise` branch is optional:**

```
choose if status of order1 is active: show "active order"
```

If the condition is false, the `choose` statement produces no output and no side effects. No error — the statement completes silently. This matches English intuition: "if it's active, show it" — no instruction for the false case means no action.

---

### §100 — `choose` CONDITIONS: VALUE EXPRESSIONS WITH EXISTING OPERATORS

**Decision: Conditions in `choose if` clauses use value expressions on both sides of the operator, evaluated once against the current symbol table state. The operators are unchanged — no new condition syntax. LOCKED as `choose` condition specification.**

In `filter`/`keep`, the `where` clause condition references fields on list items implicitly — `where total is above 50` means "check each item's `total` field." The `where` clause has a target list that provides context.

`choose` has no target list. Its condition references values explicitly — everything is a direct symbol-table lookup or field-access expression.

**Condition patterns:**

```
# Named scalar
choose if count-result is above 50: show "many"

# Field access via 'of' (v2a §68 / v2b §77)
choose if total of order1 is above 50: show "big order"

# Compare two values
choose if total of order1 is above total of order2: show "order1 is bigger"

# String comparison with quoted value (v2c §85)
choose if status of order1 is "in progress": show "still working"

# Compound condition with and/or
choose if total of order1 is above 50 and status of order1 is active: show "big and active"
```

**Operators:** `is` (equality), `is above` (greater than), `is below` (less than), `is equal to` (equality, long form), `is not above` (less than or equal), `is not below` (greater than or equal), `is not equal to` (not equal). All unchanged from inception §21.

**`and`/`or` in conditions:** Inside the condition (between `if` and `:`), `and` and `or` create compound conditions, same as in `where` clauses (inception §21, rule 2). Mixed `and`/`or` triggers the amber precedence prompt (v1a §30). The colon terminates the condition — `and`/`or` after the colon are in action context (§101), not condition context.

**Semantic checks:** Both sides of the condition must resolve to values. If a name doesn't exist, the interpreter produces the existing missing-name error. If a field-access fails, the existing §68 semantic checks apply. Type mismatches in comparisons (comparing a number to a string) produce the existing type-mismatch error.

---

### §101 — MULTI-WAY BRANCHING AND MULTI-STATEMENT ACTIONS

**Decision: `otherwise if` chaining supports multi-way branching. `and` inside branches supports multi-statement actions. The colon is the context switch between condition mode and action mode. LOCKED as `choose` branching and sequencing rules.**

**Multi-way branching:**

```
choose if status of order1 is active: show "escalate" otherwise if status of order1 is pending: show "wait" otherwise show "archive"
```

The grammar is recursive: `otherwise` is followed by either an action (terminal alternative) or `if <condition>: <action>` (another branch). The parser, after consuming `otherwise`, peeks ahead. If the next token is `if`, it parses another condition-action pair. If not, it parses a terminal action.

**Evaluation is short-circuit.** The interpreter checks conditions in order and executes the first matching branch. Once a branch fires, remaining conditions are not evaluated and remaining actions are not executed. This matches English intuition — "if X do A, otherwise if Y do B, otherwise do C" implies trying each condition in sequence and stopping at the first match.

**Multi-statement actions:**

```
choose if total of order1 is above 50: show "big order" and remember a value called flag with big otherwise show "small order" and remember a value called flag with small
```

After the colon, `and` means operation sequencing (inception §21, rule 3) — "also do this in the same branch." `otherwise` ends the current branch. End of line ends the final branch.

**Context switch at the colon:**

| Position | `and`/`or` meaning |
|---|---|
| Between `if` and `:` | Compound condition (inception §21, rule 2) |
| After `:` (inside consequence) | Operation sequencing (inception §21, rule 3) |
| After `otherwise` + `if`, between `if` and `:` | Compound condition |
| After `otherwise` + `:` | Operation sequencing |

The colon is the delimiter that switches context. The parser tracks whether it is inside a condition or inside an action. This is consistent with the clause-context tracking mechanism in v1c §51.

**One-line constraint.** The language's one-statement-per-line rule (inception §22) means multi-way `choose` statements must fit on one line. This provides a natural complexity cap (§19, Mechanism 4) — very long chains are syntactically valid but practically bounded by readability. If the interpreter's post-parse complexity suggestion fires, it applies to `choose` statements like any other.

---

### §102 — `choose` IS SIDE-EFFECT ONLY; `choose` INSIDE `each` DEFERRED

**Decision: `choose` is a side-effect-only verb. It does not produce a return value. When `choose` is the last operation in a composition body and that composition is called in value position, the interpreter produces the v2b §76 error. LOCKED as `choose` value semantics.**

The updated side-effect-only list (extending v2b §76):

| Verb | Side effect |
|---|---|
| `show` (inception §17) | Emits display output |
| `filter` (inception §17 / §24) | Mutates the target list in place |
| `each` (inception §17) | Iterates the collection, running its body per item |
| `remember` (inception §17) when not a `from <verb-phrase>` form | Stores a value in the symbol table |
| `remember how to <name>: <body>` | Stores a composition definition |
| **`choose`** (this section) | Evaluates a condition and executes one branch |

Error when used as last operation in a composition called in value position:

> *"Composition '<name>' doesn't return a value — its last operation is 'choose', which only has side effects."*

Same wording pattern as v2b §76.

**`choose` inside `each` is deferred.** `each the orders choose if total is above 50: show "big" otherwise show "small"` is a parse error:

> *"'choose' can't appear inside 'each'. To handle items differently, use 'keep' to separate them by condition."*

The v2b §78 model clarification established that `each` iterates with `show`; list-level operations and control flow belong outside `each`. Per-item branching is conceptually coherent but expands `each`'s scope significantly. If a concrete need surfaces from dogfooding, it can be added in a future addendum. The error message guides toward the `keep`-based workaround.

---

### §103 — `transform` AND `compare` CONTINUED DEFERRAL

**Decision: `transform` and `compare` remain in the v2 deferred verb table. Their reserved-word slots are protected (v1a §29). LOCKED as continued deferral.**

Both verbs were deferred in the inception checkpoint (§21) because their semantics were under-specified. That remains the case:

- **`transform`** names a family of operations — per-item field modification, per-item arithmetic, format conversion, applying a composition to each item — each with different grammar implications. Without a concrete use case from dogfooding that says "I tried to do X and couldn't," the grammar would be speculative.
- **`compare`** names multiple concepts — sorting a collection by a field, showing differences between two values, evaluating relationships between items. The word is ambiguous enough that it might warrant two separate verbs rather than one overloaded one.

Both words remain reserved. No user program can use `transform` or `compare` as names, field names, or values (v1a §29, v1c §46). When concrete use cases surface, each verb gets its own design session with the same pattern used for `choose` — concept-layer naming (§10), word salad test (§20), interaction analysis with existing constructs.

---

### §104 — UPDATED VOCABULARY TABLE

Updated from v2c §93 / v2b §82 / v2a §73.

| Category | Words | Count |
|---|---|---|
| **Verbs** | `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each`, `choose` | **9** |
| **Connectives** | `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`, `of`, `if`, `otherwise` | **12** |
| **Operators** | `is`, `above`, `below`, `not` (single-word) | 4 |
| **Multi-word operator component** | `equal` (combines with `to` per inception §22) | 1 |
| **Articles** | `the`, `a`, `an` | 3 |
| **v2 deferred verbs** | `transform`, `compare` | **2** |
| **v2 deferred connectives** | `when`, `unless` | 2 |
| **Total reserved** | | **33** |

Delta from v2c §93: +1 verb (`choose` promoted from deferred), +2 connectives (`if`, `otherwise`). Deferred verbs: 3 → 2 (`choose` promoted). Reserved word count: 31 → 33.

**Verb signatures** (extending inception §17 / v2a §73):

| Verb | Slots |
|---|---|
| `remember` | name, value |
| `show` | target |
| `filter` | target, condition |
| `keep` | target, condition |
| `count` | target |
| `gather` | name, from, to |
| `combine` | target |
| `each` | collection, action |
| `choose` | condition (after `if`), consequence (after `:`), alternative (after `otherwise`, optional) |

**Composition signature** (extending inception §17):

Compositions now have an optional parameter slot: `remember how to <name> [from <param>]: <body>`. Compositions without `from` have no parameter (existing behavior). Compositions with `from <param>` have a single named parameter.

---

### §105 — NEW TEST SENTENCES

Extending the test suite from sentence 80 (v2c §94) to sentence 95.

**Sentence 81 — Basic composition parameter**
```
remember an order called o1 with total as 75 and status as active
remember an order called o2 with total as 30 and status as pending
remember a list called orders with o1 and o2
remember how to find-big from data: keep the data where total is above 50
find-big from orders
```
→ Line 5 auto-shows: `total: 75, status: active` (one match)
**Tests:** §96 — named parameter, call with `from`, body references parameter.

**Sentence 82 — Parameter doesn't affect source (copy semantics)**
```
remember an order called o1 with total as 75 and status as active
remember an order called o2 with total as 30 and status as pending
remember a list called orders with o1 and o2
remember how to destroy from data: filter the data where total is above 50
destroy from orders
count the orders
```
→ Line 5: `total: 75, status: active` (filter auto-shows the match)
→ Line 6: `2` (orders unchanged — filter mutated the parameter's copy, not the original)
**Tests:** §96 — copy semantics. The composition's `filter` mutates `data` (the local copy), not `orders` (the global original).

**Sentence 83 — Parameter shadows global name**
```
remember a value called data with 999
remember an order called o1 with total as 75 and status as active
remember a list called items with o1
remember how to inspect from data: count the data
inspect from items
show data
```
→ Line 5: `1` (count of items, which was passed as `data`)
→ Line 6: `999` (global `data` restored after call)
**Tests:** §96 — parameter shadows global, global restored after call.

**Sentence 84 — Parameterized composition returns value**
```
remember an order called o1 with total as 75 and status as active
remember an order called o2 with total as 30 and status as pending
remember a list called orders with o1 and o2
remember how to find-big from data: keep the data where total is above 50
remember the results called big from find-big from orders
count big
```
→ Line 6: `1`
⊕ Symbol table: `big` = list with one record (o1).
**Tests:** §98 — parameterized call in value-capture position. Two `from` tokens disambiguated correctly.

**Sentence 85 — Error: expected parameter not provided**
```
remember how to find-big from data: keep the data where total is above 50
find-big
```
⚠ Outcome 5: *"'find-big' expects an input (from <data>). Try: find-big from <your-list>."*
**Tests:** §97 — parameter mismatch error (expected, not provided).

**Sentence 86 — Error: unexpected parameter provided**
```
remember how to show-all: show orders
show-all from tasks
```
⚠ Outcome 5: *"'show-all' doesn't take an input. Call it on its own: show-all."*
**Tests:** §97 — parameter mismatch error (not expected, provided).

**Sentence 87 — `remember` inside parameterized composition writes to global scope**
```
remember an order called o1 with total as 75 and status as active
remember a list called items with o1
remember how to process from data: count the data and remember a value called last-count with 42
process from items
show last-count
```
→ Line 4: `1` (count auto-shows)
→ Line 5: `42` (remember wrote to global scope)
**Tests:** §96 — only the parameter is local; `remember` inside the body writes globally.

**Sentence 88 — Basic choose if/otherwise**
```
remember a value called score with 75
choose if score is above 50: show "pass" otherwise show "fail"
```
→ Line 2: `pass`
**Tests:** §99 — basic `choose if ... : ... otherwise ...`.

**Sentence 89 — Choose without otherwise, condition false**
```
remember a value called score with 30
choose if score is above 50: show "pass"
show "done"
```
→ Line 3: `done`
**Tests:** §99 — `otherwise` branch omitted, condition false, no output from `choose`, execution continues.

**Sentence 90 — Choose with field-of-record condition**
```
remember an order called o1 with total as 75 and status as active
choose if total of o1 is above 50: show "big order" otherwise show "small order"
```
→ Line 2: `big order`
**Tests:** §100 — condition uses `of` value expression.

**Sentence 91 — Multi-way branching with otherwise if**
```
remember a value called level with 5
choose if level is above 8: show "high" otherwise if level is above 3: show "medium" otherwise show "low"
```
→ Line 2: `medium` (first condition false, second true, short-circuit)
**Tests:** §101 — `otherwise if` chaining with short-circuit evaluation.

**Sentence 92 — Multi-statement action with and**
```
remember a value called score with 75
choose if score is above 50: show "pass" and remember a value called result with pass otherwise show "fail" and remember a value called result with fail
show result
```
→ Line 2: `pass`
→ Line 3: `pass`
**Tests:** §101 — `and` for operation sequencing inside the consequence branch.

**Sentence 93 — Choose with quoted string in condition**
```
remember a task called t1 with status as "in progress"
choose if status of t1 is "in progress": show "still working" otherwise show "done"
```
→ Line 2: `still working`
**Tests:** §100 — quoted string in condition, combined with v2c quoting.

**Sentence 94 — Choose inside each is an error**
```
remember an order called o1 with total as 75 and status as active
remember a list called orders with o1
each the orders choose if total is above 50: show "big"
```
⚠ Outcome 4: *"'choose' can't appear inside 'each'. To handle items differently, use 'keep' to separate them by condition."*
**Tests:** §102 — `choose` inside `each` deferred.

**Sentence 95 — Choose as last op in composition, used in value position**
```
remember a value called score with 75
remember how to check: choose if score is above 50: show "pass"
remember the result called r from check
```
⚠ Outcome 5: *"Composition 'check' doesn't return a value — its last operation is 'choose', which only has side effects."*
**Tests:** §102 — `choose` is side-effect only, same pattern as v2b §76.

---

### §106 — UPDATED BUILD BOUNDARY (extension to v2c §95)

The v2c build boundary is extended (not replaced):

| Component | v2d additions |
|---|---|
| **Lexer** | `choose` reclassified from DEFERRED_VERB to VERB. `if` and `otherwise` added as CONNECTIVE tokens. |
| **Parser** | Composition definition: parse optional `from <param-name>` between composition name and colon. Composition call (standalone): parse `<comp-name> from <name>` as parameterized call. Value-capture with parameterized call: peek-ahead after UNKNOWN in value-capture position to detect `from` (§98). `choose` statement: parse `choose if <condition> : <action> [otherwise [if <condition> :] <action>]*`. Condition parsed between `if` and `:` using value-expression operands. Action parsed after `:` with `and` for operation sequencing. `otherwise` triggers alternative or chained branch. `choose` inside `each` rejected with error. |
| **Semantic analyzer** | Parameter mismatch: at call time, check whether the composition's definition includes a parameter; error if call/definition disagree (§97). `choose` condition: validate that both sides of the condition resolve to values of comparable types. `choose` in composition return-value context: added to side-effect-only list (§102). |
| **Interpreter** | Parameter binding: save/bind/execute/restore for local scope (§96). Copy semantics for parameter value. `choose` execution: evaluate condition; if true, execute consequence; if false, execute alternative (if present) or skip. Multi-way: evaluate conditions in order, short-circuit on first match. Multi-statement actions: stepwise execution within each branch (v1d §56). |
| **Canonical renderer** | Composition definition with parameter: emit `from <param>` between name and colon. Composition call with parameter: emit `<comp-name> from <name>`. `choose` statement: emit `choose if <condition>: <action> [otherwise [if <condition>:] <action>]*`. |
| **Result interface** | Unchanged. Five outcomes per v1c §50. New errors (parameter mismatch, choose-inside-each) map to existing Outcome 4/5. |
| **CLI wrapper** | Unchanged. |

**What v2d does NOT build:**

- `transform` / `compare` (continued deferral, §103).
- `when` / `unless` and event-driven execution (still v2-deferred per inception §25).
- `choose` inside `each` (deferred per §102).
- Multiple composition parameters (deferred per §96).
- Value-expression parameters (deferred per §96).
- Nested records and chained `of` (v2b §77).
- Tile interface, proposal engine, domain packs (Branch C/E).

---

## WHAT IS LOCKED

This addendum locks:

- **Composition parameters (§96).** Named parameter declared with `from` in the definition, passed with `from` at the call site. Single parameter. Local scope for the parameter only (shadows global, restored after call). Copy semantics. Names-only as values. `from` disambiguation table extended with two new entries (parameter declaration, parameter passing). Resolves Q9 fully.
- **Parameter mismatch errors (§97).** Calling with/without a parameter when the composition doesn't/does expect one. Both Outcome 5, error at the call site before body execution.
- **Parameterized calls in value-capture position (§98).** `remember ... from comp from name` works via peek-ahead disambiguation. Three-deep nesting not supported (requires value-expression parameters).
- **`choose` verb (§99).** Grammar: `choose if <condition>: <action> [otherwise <action>]`. Two new connectives: `if`, `otherwise`. Promoted from deferred to active. Verb count: 8 → 9. Connective count: 10 → 12.
- **`choose` conditions (§100).** Value expressions on both sides of the operator. Same operators as `where` clauses. Compound conditions with `and`/`or` between `if` and `:`. No new condition syntax.
- **Multi-way branching and multi-statement actions (§101).** `otherwise if` chaining with short-circuit evaluation. `and` for operation sequencing inside branches. Colon as context switch between condition mode and action mode.
- **`choose` is side-effect only (§102).** Added to v2b §76 list. Does not return a value. `choose` inside `each` deferred.
- **`transform` and `compare` continued deferral (§103).** Reserved-word slots protected. No grammar specified.
- **Updated vocabulary (§104).** 9 verbs, 12 connectives, 33 reserved words total (was 8/10/31 in v2c).
- **Fifteen new test sentences (§105).** Sentences 81–95 extending the test suite from 80.

This addendum does NOT modify any prior locked decision. Specifically:
- `filter` remains destructive (v1d §66 / inception §24).
- `keep` remains non-destructive (v2a §67).
- `combine` remains numeric-only and non-destructive (v1b §38, §39).
- Composition return values (v2b §76) are unchanged — the side-effect-only list is extended, not redefined.
- Generalized `of` (v2b §77) is unchanged — `of` in `choose` conditions uses the same value-expression path.
- The fifth `and` rule (v2a §69) is unchanged — the new `and` contexts in `choose` are operation sequencing (existing rule 3) and compound conditions (existing rule 2), not a sixth meaning.
- Quoting (v2c §85–§92) is unchanged — quoted strings work in `choose` conditions and actions via existing value-position rules.
- Single-token field names and composition names unchanged.
- The five-outcome taxonomy (v1c §50) unchanged.
- Stepwise execution (v1d §56) unchanged — applies within `choose` branches.

---

## RESUME PROMPT (Inscript Programming Language v2d)

*We are resuming from the Inscript Programming Language Composition Parameters and Conditional Branching Addendum v2d (May 12, 2026), which extends v2c Multi-Word Strings (May 12, 2026), and back through v2b/v2a/v1d/v1c/v1b/v1a and the Inception Checkpoint v1 (all May 11–12, 2026). v2d resolves two open design questions: **Q9 (composition parameters)** and the **`choose` verb** (promoted from deferred). **Composition parameters**: named parameter declared with `from` in the definition (`remember how to find-big from data: ...`), passed with `from` at the call site (`find-big from orders`). Single parameter, local scope (shadows global, restored after call), copy semantics, names-only. Two parameter-mismatch errors at the call site. Parameterized calls work in value-capture position (`remember ... from comp from name`) via peek-ahead disambiguation. `from` disambiguation table extended to five entries. **`choose` verb**: grammar `choose if <condition>: <action> [otherwise <action>]`. Two new connectives: `if` (introduces condition) and `otherwise` (introduces alternative). Conditions use value expressions with existing operators — no new condition syntax. Multi-way branching via `otherwise if` chaining with short-circuit evaluation. Multi-statement actions via `and` sequencing inside branches, colon as context switch. `choose` is side-effect only (added to v2b §76 list). `choose` inside `each` deferred. **`transform` and `compare` remain deferred** — reserved-word slots protected, no grammar specified, waiting for concrete use cases. **Vocabulary**: 9 verbs, 12 connectives, 33 reserved words (was 31). Fifteen new test sentences (81–95). Build specification is now nine documents: inception checkpoint v1, addenda v1a/v1b/v1c/v1d/v2a/v2b/v2c/v2d, plus the 95-sentence test suite. The sequential feature set is now structurally complete: sequence (`and`), iteration (`each`), filtering (`filter`/`keep`), branching (`choose`), reuse with parameters (compositions + `from`), field access (`of`), and data expression (quoting). The remaining language work is event-driven execution (`when`/`unless`, Branch F) and the deferred verbs when concrete use cases surface.*

---

## PROVENANCE NOTE

This addendum was verified against:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026):
  - §10 (concept-layer vocabulary) — `choose` names what the user is trying to do (make a decision). `if` and `otherwise` are concept-layer words, not mechanism-layer.
  - §17 (verb signatures, slot filling) — `choose` signature added: condition + consequence + alternative.
  - §19 (vocabulary scaling) — two new connectives within the clarity budget. The word salad test (§20) passes trivially for `if` and `otherwise`.
  - §21 (parser rules, `and`/`or` disambiguation) — `and`/`or` inside `choose` conditions reuse rule 2 (compound conditions). `and` inside `choose` actions reuses rule 3 (operation sequencing). No sixth `and` meaning.
  - §22 (lexer specification) — colon delimiter reused for `choose` condition/action separation, consistent with composition definitions. Case normalization applies to `if` and `otherwise`.
  - §23 (composition validation split) — parameter declaration is grammar-checked at definition time; parameter mismatch is checked at call time. Consistent with the existing split.
  - §24 (copy semantics) — parameter receives a deep copy. Consistent with all data operations.
  - §25 (v1/v2 deferral table) — `choose` promoted from deferred to active. Q9 fully resolved. `transform` and `compare` remain deferred.
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026):
  - §29 (reserved word list) — extended with `if` and `otherwise`. `choose` moves from deferred to active. Total: 33.
  - §30 (mixed-precedence amber) — applies to compound `and`/`or` conditions inside `choose if` clauses, same as `where` clauses.
- **`inscript_addendum_v1b_design_resolutions.md`** (May 11, 2026):
  - §41 (composition call syntax) — extended by §96 (parameter declaration) and §98 (parameterized call in value position). Composition chaining (`<name> from <other>` for parameter passing) is now the resolved form of Q9 — not the deferred form.
  - §43 (`from` disambiguation) — extended with two new entries (parameter declaration, parameter passing). Existing three meanings unchanged.
  - §44 (complete disambiguation ruleset) — extended with `from` entries and the `if`/`otherwise`/`:` context rules for `choose`.
- **`inscript_addendum_v1c_implementation_hardening.md`** (May 11, 2026):
  - §50 (five-outcome taxonomy) — new errors map to existing Outcome 4/5. No new outcome categories.
  - §51 (parser lookahead) — peek-ahead in §98 uses the existing lookahead capability.
  - §52 (deterministic interpretation only) — invoked for parameter-mismatch errors (§97) and the reject-silent-ignore principle.
- **`inscript_addendum_v1d_build_boundary.md`** (May 11, 2026):
  - §56 (stepwise execution) — applies within `choose` branches. Multi-statement actions in branches commit independently.
  - §57 (case normalization) — `if` and `otherwise` are lowercased by the lexer like all tokens.
  - §65/§66 (test sentences, build boundary) — extended through v2a/v2b/v2c, now §105/§106.
- **`inscript_addendum_v2a_dogfooding_resolutions.md`** (May 12, 2026):
  - §67 (`keep` verb) — `keep` inside a parameterized composition is the primary reuse pattern.
  - §68/v2b §77 (`of` connective) — `of` value expressions work in `choose` conditions via existing value-expression paths.
  - §69 (fifth `and` rule) — unchanged. `and` in `choose` branches is operation sequencing (rule 3), not a new meaning.
  - §70 (composition chaining error) — v2a §70's error message for `<comp> from <value>` is now superseded: this is the resolved parameter-passing syntax, not a deferred feature. The error wording from v2a §70 should be removed from the implementation — it is replaced by either successful parameter passing or the §97 mismatch errors.
  - §73 (vocabulary table) — updated in §104 to 33 reserved words.
- **`inscript_addendum_v2b_composition_returns.md`** (May 12, 2026):
  - §76 (composition return values) — the side-effect-only list is extended with `choose` (§102). The value-producing list is unchanged — parameterized compositions return values the same way as non-parameterized ones (the last operation's value).
  - §78 (list/iteration model, `each` scope) — referenced in §102 for the `choose`-inside-`each` deferral.
  - §84 (build boundary) — extended through v2c §95, now §106.
- **`inscript_addendum_v2c_multi_word_strings.md`** (May 12, 2026):
  - §85–§92 (quoting mechanism) — quoted strings work in `choose` conditions and actions via existing value-position rules. No interaction.
  - §95 (build boundary) — extended in §106.
- **Filename:** `inscript_addendum_v2d_parameters_and_branching.md` — domain `inscript` (provisional, pre-vault), class `addendum`, version `v2d` (fourth in the v2 series, following v2a/v2b/v2c), subtitle `parameters_and_branching`.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE COMPOSITION PARAMETERS AND CONDITIONAL BRANCHING ADDENDUM v2d*

*May 12, 2026*

*v2a gave the language reuse with `keep`. v2b gave compositions return values. v2c gave the language its first syntax mark.*
*v2d gives compositions their input — and gives the language its last control flow construct.*
*Sequence, iteration, filtering, branching, reuse with parameters. The sequential feature set is structurally complete.*
*The next chapter is the one that changes the interpreter's fundamental model: event-driven execution.*
*But that chapter can wait. The language can already express what its target users need to express.*
