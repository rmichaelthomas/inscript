# ADDENDUM
## Inscript Programming Language — Composition Returns and Generalized Field Access
### v2b — Completing the Reuse Story

**Status:** LOCKED — EXTENDS `inscript_addendum_v2a_dogfooding_resolutions.md`
**Date:** May 12, 2026
**Author:** Rob Thomas / R. Michael Thomas
**Document type:** Addendum — adds composition return values (D9), generalizes the `of` connective to all value positions (D11), clarifies the list/iteration model (D10), and locks small improvements from the v2a dogfooding (U7, U8, U9)
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Extends `inscript_addendum_v2a_dogfooding_resolutions.md` (May 12, 2026), which extends v1d/v1c/v1b/v1a and the Inception Checkpoint v1 (May 11, 2026). Continues from §75. Implements decisions F, G, H, I, K from the v2b Design Triage (`inscript_v2b_design_triage_2026_05_12.md`, May 12, 2026), which triaged the six gaps surfaced by the v2a dogfooding pass (`inscript_gap_inventory_2026_05_12_v2a_dogfooding.md`, same date). Two of those gaps (U7, U8) shipped as v2.1-patches before this addendum was drafted; they are locked here for spec completeness. The remaining four (D9, D10, D11, U9) are locked here for the first time.

---

## HOW TO READ THIS DOCUMENT

- §76 locks **D9** (composition return values) — the structural priority of v2b. Path A: a composition returns the value of its last operation. Sub-decision G: error at the call site when the last operation is void-result.
- §77 locks **D11** (generalize `of`) — the `<field> of <record>` form is now a valid value-expression anywhere a value or field reference is expected. Sub-decision I: single-level only.
- §78 locks **D10** (list/iteration model clarification) — names the v1/v2/v2b model (list operations only; per-record decisions belong in the where-clause). The v2.1-patch error wording (already shipped) is referenced.
- §79 locks **U7** (duplicate fields in multi-field show rejected at semantic-analysis time). Shipped as a v2.1-patch.
- §80 locks **U8** (`of`-on-list error suggests `each`). Shipped as a v2.1-patch.
- §81 locks **U9** (operation-sequencing display semantics — documentation note, no behavior change).
- §82 updates the vocabulary table. **No new vocabulary in v2b.** Vocabulary count stays at 31 reserved words.
- §83 adds test sentences 60–68 to the test suite (which ended at sentence 59 in v2a §74).
- §84 extends the build boundary (v2a §75).

---

### §76 — D9: COMPOSITION RETURN VALUES

**Decision: A named composition returns the value of its last operation when used in a value position (`remember the X from <composition-name>`). The body's earlier operations still run for their side effects. When the last operation is purely side-effect (`show`, `filter`, `each`, `remember`, `remember how to`), using the composition in a value position is a semantic error at call time. LOCKED as v2b composition semantics. Resolves Q9 (composition reuse) for the value-flow direction.**

The gap (v2a dogfooding D9): the v2a `keep` verb made compositions a natural reuse unit — `remember how to find-major: keep the docs where words is above 7000` defines a reusable filter. But `remember the heavy called heavy from find-major` errored with *"Composition calls can't be used as a value in this version."* Users had to inline the `keep` body verbatim, defeating the reuse purpose.

The decision in the v2b Design Triage §3 was Path A (architect Q&A F): a composition's return value is the value of its last operation. Path B (an explicit `give`/`return` marker) was rejected — it would have added vocabulary for something the existing `gather`/`combine`/`count` auto-return pattern already covers.

**Composition return rule.** When the parser encounters `<composition-name>` after `from` in `remember ... from <composition-name>`, it already wraps the call in `CompositionCallNode` (v1b §41 fallback). In v2b, the interpreter's expression evaluator treats `CompositionCallNode` as a value-producing expression: it executes the composition's body and returns the value of the last operation.

**Value-producing last operations.** These verbs return a value when they appear as the last operation of a composition body:

| Verb | Returned value |
|---|---|
| `keep` (v2a §67) | The list of matching items |
| `combine` (v1b §38) | The numeric sum of the target list |
| `count` (inception §17) | The number of items in the target list |
| `gather` (inception §17 / v1b §40) | The constructed list of numbers |
| `remember ... from <verb-phrase>` (v1b §43) | The captured value |
| `<composition-name>` (this section) | The recursive return value |

**Side-effect-only last operations.** These verbs do not produce a captured value when used as the last operation of a composition body:

| Verb | Side effect |
|---|---|
| `show` (inception §17) | Emits display output |
| `filter` (inception §17 / §24 line 478) | Mutates the target list in place |
| `each` (inception §17) | Iterates the collection, running its body per item |
| `remember` (inception §17) when not a `from <verb-phrase>` form | Stores a value in the symbol table |
| `remember how to <name>: <body>` | Stores a composition definition |

**Error at call site.** Architect Q&A G locks the error path. When a composition with a side-effect-only last operation is called via `remember ... from <name>`, the interpreter produces a semantic error (Outcome 5 per v1c §50):

> *"Composition '<name>' doesn't return a value — its last operation is '<verb>', which only has side effects."*

The side effects of the composition's body do not execute when this error fires — the error is structural and detected before body execution. (Compare: v1b §41 locks call-time name resolution, so structural-error detection of this kind has precedent.)

**Multi-operation bodies.** When the composition body is a `SequenceNode` (multiple operations joined by `and` — v1d §56 stepwise execution), the interpreter executes each non-final operation for its side effects, then evaluates the final operation for its return value. Stepwise semantics apply: if a non-final operation fails, the failure surfaces as the composition's failure, and the final operation does not execute.

**Standalone calls unchanged.** A bare composition call as a statement (`find-major` on its own line) still executes for its side effects exactly as in v2a §67 — the body's auto-show, mutations, and stored values all happen. The new rule only applies in value position (after `from` in `remember ... from <name>`).

**Composition chaining still deferred.** v1b §41 and v2a §70 keep `<name> from <other>` as a v2-design item (composition parameters). v2b §76 unlocks a *different* shape — `remember ... from <name>` — without unlocking parameter passing. The two are independent.

**Why Path A:** matches the language's existing auto-return pattern (`gather`/`combine`/`count`); requires no new vocabulary; keeps the reserved-word count at 31 (§82). The vocabulary budget is the clarity budget (inception §19, §20).

---

### §77 — D11: GENERALIZE `of` TO VALUE POSITIONS

**Decision: The `of` connective extends from v2a §68's `show <field> of <record>` form to any value or field-reference position. `<field> of <record>` is a valid value-expression after `with`, after operators in `where` clauses, and anywhere else a single value is expected. Single-level only — chained `of` (`field-a of field-b of record`) remains a parse error. LOCKED as v2b value-expression form.**

The gap (v2a dogfooding D11): natural prose expressions like `keep the docs where words is above words of doc-1` and `remember a copy called holder with total of order1` failed to parse because `of` was only consumed in `_parse_show`. v2a §68 deliberately scoped `of` to `show` as a starting point; v2b lifts that scope to all value positions.

The decision in the v2b Design Triage §4 was Path H: generalize once. The single parser rule is simple, the disambiguation is unambiguous (after a NAME, `of` always means field access — no other meaning), and incremental rollout would have caused interaction problems with the existing show-only path.

**The general value-expression rule.** When the parser encounters an UNKNOWN token in a value position or a field-reference position, and the next token is `of` (CONNECTIVE), it consumes `of` and then the next UNKNOWN as the record name. The result is a field-access value-expression.

**Disambiguation.** Adding the fifth value-form to the parser's expression-position rules:

| Value-position shape | Meaning | Disambiguation |
|---|---|---|
| `<NUMBER>` | Numeric literal | Single NUMBER token |
| `<UNKNOWN>` not followed by `of` | Bare word — string literal or name reference (v1c §46) | After consuming UNKNOWN, peek does not see `of` |
| `<UNKNOWN> of <UNKNOWN>` | Field-access value: extract the field from the record (this section) | After consuming the first UNKNOWN, next token is the CONNECTIVE `of`; consume it and the next UNKNOWN as the record name |
| `each` (inside `where`) | Iterator pronoun (v1b §37) | Parser state is inside a `where` clause |
| `<verb-phrase>` (after `from` in `remember`) | Recursive-descent value capture (v1b §43) | Active verb = `remember`, intro = `from`, next token = VERB |

The new rule does not collide with any existing meaning. `of` has no meaning *other* than field access in v2b. The disambiguation is a one-token lookahead consistent with v1c §51's parser capability requirements.

**Semantic checks.** The same three checks from v2a §68 apply at any usage site:

1. The record name resolves to a symbol in the symbol table (else: *"I can't find '<name>'. You might need to 'remember' it first."* — Outcome 5).
2. The resolved symbol is a record (else: *"'of' needs a record. '<name>' is <type>."* — for list-of-records targets, U8 wording: *"...is a list of records — did you mean: each the <name> show <field>?"*).
3. The record's schema contains the requested field (else: *"'<record>' doesn't have a field called '<field>'."*).

These checks fire at semantic-analysis time and produce Outcome 5 errors (v1c §50). The interpreter never executes a malformed field access.

**Single-level only.** Architect Q&A I locks: `<field-a> of <field-b> of <record>` is a parse error in v2b. Nested records are not a v1/v2/v2b data shape — records are flat field→value maps (v1d §60). Chained `of` belongs in the same future session that defines nested records. Rejecting chains until then keeps the spec deterministic and prevents users from writing programs that "work" syntactically but have no defined semantics.

**Parser error for chained `of`:** *"Field access uses one record at a time: `<field> of <record>`. Chained forms (`a of b of c`) need nested records, which v2b doesn't yet have."*

**Interaction with v2a §68.** The existing `show <field> of <record>` form is a special case of the general rule. The implementation may either keep the existing `_parse_show` branch and add the general rule elsewhere, or refactor `_parse_show` to use the general rule. The user-visible behavior is identical.

**Interaction with D7 (multi-word strings, v2a §72).** Still deferred. The forward-compatibility note in v2a §68 remains: when D7 is taken up, the chosen approach extends what constitutes a valid field/record name; `of` itself doesn't need revisiting.

---

### §78 — D10: LIST/ITERATION MODEL CLARIFICATION

**Decision: v1/v2/v2b uses list-level filtering. `keep` and `filter` operate on a whole list and a single where-clause condition. Per-item decision logic lives in the where-clause, not in an `each` body. LOCKED as model clarification (no language surface added).**

The gap (v2a dogfooding D10): `each the docs keep where words is above 9000` errored at parse, but the error message didn't tell the user that the construct was structurally meaningless. On closer triage (v2b Design Triage §5), this isn't a missing feature — it's a category mismatch:

- `keep` and `filter` are *list operations* (target = a list; condition = one `where` clause that runs against each item).
- `each` is an *iteration* (one item at a time).
- "Inside `each`, do `keep`" has no list to operate on per iteration.

The user's intent ("decide each item conditionally") is already expressible at the list level:

```
each the docs keep where words is above 9000     # category error
keep the docs where words is above 9000          # the intended workflow
```

**The model statement.** v1/v2/v2b business-rules and compliance use cases are list-shaped. The four pieces:

1. `keep` and `filter` are list operations. They take a list target and a `where` clause that evaluates per item.
2. `each` is a display iteration. Its sub-operation is `show`, possibly with multiple fields (v2a §69).
3. Per-item *decision logic* lives in the `where` clause of a list operation.
4. Per-item *display logic* lives in the body of `each ... show ...`.

**No `each ... do <verb>` deferral.** Architect Q&A K locks closing the door, not deferring. If a future use case emerges that the `where` clause genuinely cannot express (per-item state, per-item side effects beyond display), it can be reopened as a fresh design item with its own grammar. As of v2b, no concrete such use case exists.

**Error wording.** The v2.1-patch (shipped between v2a and v2b) extended `_consume_target` to detect `keep` or `filter` inside an `each` clause and emit the list-level guidance:

> *"'keep' is a list operation — it can't appear inside 'each'. To keep only some items, use 'keep <list> where <condition>' directly."*

Same wording for `filter`. LOCKED here for spec completeness.

---

### §79 — U7: REJECT DUPLICATE FIELDS IN MULTI-FIELD SHOW

**Decision: When `each ... show <field> and <field> ...` lists the same field name more than once, the semantic analyzer produces an error. The display layer does not emit duplicate columns. LOCKED as v2b semantic check (shipped as v2.1-patch). Extends v2a §69.**

The gap (v2a dogfooding U7): `each the docs show domain and class and class` produced `domain: X, class: Y, class: Y` per record — two identical columns. v2a §69 didn't lock either acceptance or rejection. Silent acceptance let typos through.

**Detection.** The analyzer's `_check_show` examines `[target_name, *node.extra_fields]` for repeats. If any name appears more than once, it raises Outcome 5:

> *"You listed '<field>' twice in this show. Did you mean another field?"*

The check fires before the existing schema-homogeneity validation (v1d §60), so a duplicate that also happens to be missing from some records produces the duplicate error first.

**Rationale.** Per v1c §52 (deterministic interpretation only), the interpreter doesn't guess at intent. Two identical columns serve no v1/v2/v2b purpose — there's no aliasing, no aggregation, no per-column formatting. Erroring is safer than emitting noise the user almost certainly didn't want.

---

### §80 — U8: `of`-ON-LIST ERROR SUGGESTS `each`

**Decision: When `show <field> of <name>` resolves `<name>` to a `list_of_records`, the analyzer emits a guidance error suggesting the `each` alternative rather than the generic type-mismatch wording. LOCKED as v2b error wording (shipped as v2.1-patch). Extends v2a §68.**

The gap (v2a dogfooding U8): `show class of docs` (where `docs` is a list) emitted *"'of' needs a record. 'docs' is a list of records."* — technically correct but not actionable. The user's intent is almost always "show this field per row."

**The new wording.**

> *"'of' needs a single record. '<name>' is a list of records — did you mean: each the <name> show <field>?"*

The suggestion uses the user's actual list and field names — drop-in replacement.

**Scope.** Only the `list_of_records` case takes the suggestion form. Scalar `of` errors (`show field of <number>`) keep the generic type-mismatch wording per v2a §68 — there's no obvious alternative to suggest.

---

### §81 — U9: OPERATION-SEQUENCING DISPLAY SEMANTICS

**Decision: When a single sentence sequences multiple verbs via `and` (v1d §56 stepwise execution), each verb runs to completion in order — including its display output. No verb's auto-show is suppressed by what follows. LOCKED as documentation note (no behavior change).**

The observation (v2a dogfooding U9): `keep the docs where words is above 9000 and show docs` emitted six lines — the three matches from `keep` (auto-show) followed by the three records from `show docs`. The user might have wanted only one or the other.

This is by design, consistent with v1d §56 (stepwise execution). Suppressing the first verb's auto-show on sequencing would be a behavior change that interacts with the locked stepwise semantics — it isn't a v2b-scoped change.

**The recommended idiom for suppressing `keep`'s auto-show:**

```
remember the matches called matches from keep the docs where words is above 9000
show matches                                                # only one display
```

The `remember ... from keep ...` capture form silences `keep`'s auto-show because the value flows into the surrounding `remember` (no standalone display). This pattern is the v2b answer to "I want to capture without displaying."

**The recommended idiom for displaying both:**

```
keep the docs where words is above 9000 and show docs       # both display
```

Operation sequencing is the explicit form when both outputs are wanted.

---

### §82 — UPDATED VOCABULARY TABLE

No vocabulary changes in v2b. The table from v2a §73 remains current:

| Category | Words | Count |
|---|---|---|
| **Verbs** | `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each` | 8 |
| **Connectives** | `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`, `of` | 10 |
| **Operators** | `is`, `above`, `below`, `not` (single-word) | 4 |
| **Multi-word operator component** | `equal` (combines with `to` per inception §22) | 1 |
| **Articles** | `the`, `a`, `an` | 3 |
| **v2 deferred verbs** | `transform`, `choose`, `compare` | 3 |
| **v2 deferred connectives** | `when`, `unless` | 2 |
| **Total reserved** | | **31** |

Architect decision F (Path A for D9) explicitly preserved the vocabulary count. Path B would have added one verb (`give` or similar) to 32; the recommendation against B is in v2b Design Triage §3.

Verb signatures (extending inception §17 / v2a §73): unchanged. `keep` and `filter` share the `target + condition` signature. The new D9 semantics are interpreter behavior, not signature changes.

---

### §83 — NEW TEST SENTENCES

Extending the test suite from sentence 59 (v2a §74) to sentence 68.

**Sentence 60 — D9 basic: capture a composition's return value**
```
remember an order called o1 with total as 75 and status as active
remember an order called o2 with total as 30 and status as active
remember a list called orders with o1 and o2
remember how to find-big: keep the orders where total is above 50
remember the big called big from find-big
count the big
count the orders
```
→ Line 6: `1` (one matching record captured into `big`)
→ Line 7: `2` (orders unchanged — D2 / §67 still holds)
**Tests:** §76 — composition's last op (`keep`) returns its matched list; capture via `remember ... from <name>` works.

**Sentence 61 — D9 chained narrowing across compositions**
```
remember an order called o1 with total as 75 and status as active
remember an order called o2 with total as 30 and status as active
remember an order called o3 with total as 100 and status as pending
remember a list called orders with o1 and o2 and o3
remember how to find-big: keep the orders where total is above 50
remember the big called big from find-big
remember how to find-active: keep the big where status is active
remember the result called result from find-active
count the result
```
⊕ `result` = list with 1 record (o1: total=75, status=active).
→ Line 9: `1`
**Tests:** §76 — chaining via captured intermediate. Each composition returns its `keep`'s matched list; chaining is achieved by capturing and using as the next composition's source.

**Sentence 62 — D9 void-result composition (semantic error)**
```
remember an order called o1 with total as 75 and status as active
remember a list called orders with o1
remember how to show-totals: each the orders show total
remember the X called X from show-totals
```
⚠ Outcome 5: "Composition 'show-totals' doesn't return a value — its last operation is 'each', which only has side effects."
**Tests:** §76 / architect Q&A G — composition with side-effect-only last op (`each`) errors when used in value position. Side effects (the display in this case) do not execute when this error fires.

**Sentence 63 — D11 `of` in a `where` clause**
```
remember an order called baseline with total as 100 and status as active
remember an order called o1 with total as 75 and status as active
remember an order called o2 with total as 150 and status as pending
remember a list called orders with o1 and o2
keep the orders where total is above total of baseline
```
→ Line 5: auto-shows the 1 record with total > 100 (o2).
**Tests:** §77 — `of` as a value expression in a `where` clause. The disambiguation rule (after a NAME in value position, peek for `of`) fires at the value-after-operator slot.

**Sentence 64 — D11 `of` in a `with` clause value position**
```
remember an order called o1 with total as 75 and status as active
remember a copy called captured-total with total of o1
show captured-total
```
→ Line 3: `75`
**Tests:** §77 — `of` as a value expression after `with`. The same rule fires for the value-position-after-`with`.

**Sentence 65 — D11 chained `of` (parse error)**
```
remember an order called o1 with total as 75 and status as active
show field-a of field-b of o1
```
⚠ Outcome 4 (parse error): "Field access uses one record at a time: <field> of <record>. Chained forms (a of b of c) need nested records, which v2b doesn't yet have."
**Tests:** §77 / architect Q&A I — single-level only; chained `of` is rejected at parse time.

**Sentence 66 — D10 model clarification (improved error wording)**
```
remember an order called o1 with total as 75 and status as active
remember a list called orders with o1
each the orders keep where total is above 50
```
⚠ Outcome 4 (parse error): "'keep' is a list operation — it can't appear inside 'each'. To keep only some items, use 'keep <list> where <condition>' directly."
**Tests:** §78 — the v2.1-patch error wording. Was shipped between v2a and v2b; locked here.

**Sentence 67 — U7 duplicate field rejected**
```
remember a doc called d1 with class as checkpoint and words as 1000
remember a list called docs with d1
each the docs show class and class
```
⚠ Outcome 5: "You listed 'class' twice in this show. Did you mean another field?"
**Tests:** §79 — duplicate field name in multi-field show is rejected.

**Sentence 68 — U8 `of`-on-list error suggests `each`**
```
remember a doc called d1 with class as checkpoint and words as 1000
remember a list called docs with d1
show class of docs
```
⚠ Outcome 5: "'of' needs a single record. 'docs' is a list of records — did you mean: each the docs show class?"
**Tests:** §80 — `of`-on-list-of-records error suggests the `each` alternative.

---

### §84 — UPDATED BUILD BOUNDARY (extension to v2a §75)

The v2a build boundary is extended (not replaced):

| Component | v2b additions |
|---|---|
| **Lexer** | No changes. `of` already lexed as CONNECTIVE per v2a §73. |
| **Parser** | `<field> of <record>` recognized as a value expression in all value positions and field-reference positions (extending the v2a §68 show-only branch). Chained `of` (a of b of c) explicitly rejected with the §77 error wording. Existing `_parse_show` path continues to handle the show-specific case. |
| **Semantic analyzer** | Composition-call-as-value (§76) — validate that the call resolves to a composition whose last operation is value-producing; otherwise emit the §76 error wording. Field-access value-expression (§77) — same three checks as v2a §68 (record exists, is a record, has the field), now at any value position. U7 (§79) — duplicate-field check in multi-field `each show`. U8 (§80) — list-of-records-specific error wording for the `of` type-mismatch path. |
| **Interpreter** | `_evaluate_expression` for `CompositionCallNode` (§76): execute the body, return the value of the last operation. Multi-op bodies execute non-final ops for side effects (v1d §56 stepwise). Field-access value-expression evaluation: look up the record, extract the field, return the value — at any value-evaluation site. |
| **Canonical renderer** | `<field> of <record>` in any value position renders as `<field> of <record>` (preserving the user's voice). Composition calls in value position render as `<composition-name>` — same as their statement form. |
| **Result interface** | Unchanged. Five outcomes per v1c §50. |
| **CLI wrapper** | Unchanged from the v2.1-patch round. |

**What v2b does NOT build:**

- Multi-word strings (D7, deferred per v2a §72).
- `transform` / `choose` / `compare` (still v2-deferred per inception §25).
- `when` / `unless` and event-driven execution (still v2-deferred).
- Composition parameters and `from` chaining (`<name> from <other-name>` — still v2-deferred per v1b §41 / Q9).
- Nested records and chained `of` (§77 sub-decision I — left for a future session).
- Per-record `each ... do <verb>` decision logic (§78 / architect K — door closed in v2b).
- Tile interface, proposal engine, domain packs (Branch C/E).

---

## WHAT IS LOCKED

This addendum locks:

- **D9 composition return values (§76).** A composition returns the value of its last operation when called in value position. Value-producing last operations: `keep`, `combine`, `count`, `gather`, `remember ... from <verb-phrase>`, nested composition calls. Side-effect-only last operations error at the call site when used in value position (architect Q&A F + G).
- **D11 generalized `of` (§77).** `<field> of <record>` is a valid value-expression anywhere a value or field reference is expected — not just after `show`. Single-level only; chained `of` is a parse error. Existing v2a §68 show-only form is a special case of the general rule (architect Q&A H + I).
- **D10 list/iteration model (§78).** v1/v2/v2b business-rules and compliance domains use list-level filtering. Per-item decision logic belongs in the `where` clause. No `each ... do <verb>` deferral — door closed in v2b (architect Q&A K). The v2.1-patch error wording for `each ... keep/filter` is locked here.
- **U7 duplicate fields rejected (§79).** Multi-field `each ... show A and A` is a semantic error. Shipped as v2.1-patch.
- **U8 `of`-on-list suggestion (§80).** `show field of <list>` suggests the `each` alternative. Shipped as v2.1-patch.
- **U9 operation-sequencing semantics (§81).** Documentation only — both outputs render when verbs are sequenced. The recommended idiom for suppression is `remember ... from keep ...`. No behavior change.
- **No vocabulary changes (§82).** 8 verbs, 10 connectives, 31 reserved words — unchanged from v2a.
- **Nine new test sentences (§83).** Sentences 60–68 extending the test suite from 59.

This addendum does NOT modify any prior locked decision. Specifically:
- `filter` remains destructive (v1d §66 / inception §24 line 478).
- `combine` remains numeric-only and non-destructive (v1b §38 / §39).
- `keep` remains non-destructive (v2a §67).
- `each`'s only sub-operation remains `show` (v2a §69, this addendum §78).
- Composition chaining (`<name> from <other>` for parameter passing) remains v2-deferred (v1b §41 / Q9 / v2a §70).
- Single-token strings remain locked for value positions (v1d §61, D7 deferred per v2a §72).
- The five-outcome taxonomy (v1c §50) is unchanged.
- Stepwise execution (v1d §56) is unchanged — §81 is documentation, not a behavior change.

---

## RESUME PROMPT (Inscript Programming Language v2b)

*We are resuming from the Inscript Programming Language Composition Returns and Generalized Field Access Addendum v2b (May 12, 2026), which extends v2a Dogfooding Resolutions (May 12, 2026), and back through v1d/v1c/v1b/v1a and the Inception Checkpoint v1 (all May 11, 2026). v2b implements decisions F, G, H, I, K from the v2b Design Triage (May 12, 2026), which triaged the six gaps from the v2a dogfooding inventory. **Six items locked**: (1) **D9 composition return values** — a composition returns the value of its last operation; matches the gather/combine/count auto-return pattern; no new vocabulary. Side-effect-only last ops (show/filter/each/remember) error at the call site when used in value position. (2) **D11 generalize `of`** to any value position; single-level only; chained `of` (a of b of c) is a parse error reserved for a future nested-records session. (3) **D10 list/iteration model clarification** — v1/v2/v2b uses list-level filtering; per-item decision logic lives in the where-clause; no `each ... do <verb>` deferral (door closed in v2b). (4) **U7 duplicate fields rejected** in multi-field `each show`. (5) **U8 `of`-on-list-of-records error** suggests the `each` alternative. (6) **U9 operation-sequencing display** — documentation only; both outputs render when verbs are sequenced. **Zero vocabulary changes** — still 8 verbs, 10 connectives, 31 reserved words. Nine new test sentences (60–68). The v2a build boundary is extended (not replaced). Build specification is now seven documents: inception checkpoint v1, addenda v1a/v1b/v1c/v1d/v2a/v2b, plus the 68-sentence test suite. The reuse story that v2a opened with `keep` is now structurally complete: define a reusable filter, call it for its side effect, capture its result via `from`, generalize field access across positions. The next open question is D7 (multi-word strings), still requiring a dedicated checkpoint.*

---

## PROVENANCE NOTE

This addendum was verified against:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026):
  - §10 (concept-layer vocabulary) — referenced in §76 for the "no new vocabulary" rationale of Path A.
  - §11 (vocabulary table) — unchanged in §82.
  - §17 (verb signatures, slot filling) — unchanged. `keep` and `filter` still share `target + condition`.
  - §19, §20 (vocabulary scaling, word salad test) — invoked for the Path-A-over-Path-B decision (F).
  - §24 (auto-show, in-place filter, copy semantics) — referenced in §76 (composition returns extend the auto-return family) and §81 (operation-sequencing display).
  - §25 (v1/v2 deferral table) including Q9 — D9 partially resolves Q9 (composition return values); composition parameters (`<name> from <other>`) remain Q9 territory.
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026):
  - §29 (reserved word list) — extended in v1c §47 to 29, v2a §73 to 31, unchanged in v2b §82.
  - §33 (canonical prose rendering) — extended in §84 for the new value-expression forms.
- **`inscript_addendum_v1b_design_resolutions.md`** (May 11, 2026):
  - §36 (descriptors are decorative) — unchanged.
  - §38, §39 (`combine` semantics) — unchanged; `combine` is a value-producing last op in §76.
  - §41 (composition call fallback) — referenced in §76 (the parser already wraps composition calls as `CompositionCallNode`; v2b changes the interpreter, not the parser). Composition chaining (`<name> from <other>` for parameters) still deferred.
  - §42 (display formats) — unchanged; §81 references the per-record display format for the multi-field path.
  - §43 (`from` disambiguation) — referenced in §76 (the recursive-descent value-capture path now also handles `CompositionCallNode` via the §76 rule).
  - §44 (complete disambiguation ruleset) — extended in §77 with the field-access value-expression rule.
- **`inscript_addendum_v1c_implementation_hardening.md`** (May 11, 2026):
  - §46 (vocabulary words cannot be string values) — unchanged.
  - §49 (iterator context for `each`) — unchanged. `each ... show` multi-field (v2a §69) and §78's model clarification both operate within the iterator-context rules.
  - §50 (five-outcome taxonomy) — §76 and §79 produce Outcome 5; §77's chained-`of` and §78's `each ... keep` produce Outcome 4. No new categories.
  - §51 (parser lookahead + clause-context tracking) — §77 uses the lookahead capability; §78's error wording uses the clause-context stack.
  - §52 (deterministic interpretation only) — invoked in §76 (error at call site for void-result rather than silent empty return) and §79 (rejecting duplicate fields rather than silently emitting noise).
- **`inscript_addendum_v1d_build_boundary.md`** (May 11, 2026):
  - §55 (reorderer scope) — unchanged.
  - §56 (stepwise execution) — referenced in §76 (multi-op composition bodies follow stepwise semantics) and §81 (operation-sequencing display documentation).
  - §57–§64 (case normalization, duplicate names, list homogeneity, schema homogeneity, single-token strings, descending ranges, range cap, structured results) — all unchanged.
  - §60 (record schema homogeneity) — referenced in §79 (U7 duplicate check fires before §60's schema check) and §77 (the field-access semantic checks).
  - §61 (single-token strings) — referenced in §77 for the D7-deferral interaction note.
  - §65 (test sentences 35–48) — extended in §74 to 59 (v2a) and now §83 to 68 (v2b).
  - §66 (build boundary) — extended (not replaced) in v2a §75, extended again in §84.
- **`inscript_addendum_v2a_dogfooding_resolutions.md`** (May 12, 2026):
  - §67 (`keep` verb) — `keep` is the most important value-producing last operation per §76. v2b unlocks `remember ... from <keep-wrapping-composition>` as the natural reuse idiom.
  - §68 (`of` connective, show-only) — extended in §77 to any value position.
  - §69 (fifth `and` rule, multi-field show) — extended in §79 with the duplicate-field check.
  - §70 (composition chaining error wording) — unchanged. `<name> from <other>` for parameter passing remains v2-deferred.
  - §71 (descriptor preservation) — unchanged. `remember the result called result from find-active` preserves "result" as the descriptor in the canonical rendering.
  - §72 (D7 deferral) — unchanged. Interaction note in §77.
  - §73 (vocabulary table) — unchanged in §82.
  - §74 (test sentences 49–59) — extended in §83 to 68.
  - §75 (build boundary) — extended in §84.
- **`inscript_gap_inventory_2026_05_12_v2a_dogfooding.md`** (May 12, 2026):
  - First-pass items D9, D10, D11, U7, U8, U9 sourced for v2b.
  - Second-pass observations confirm none of these gaps regress under the v1 UX polish; they are now resolved or documented in §76–§81.
- **`inscript_v2b_design_triage_2026_05_12.md`** (May 12, 2026):
  - §3 D9 paths (A vs B) — architect chose Path A; locked in §76.
  - §4 D11 scope and sub-decision — generalize once + single-level; locked in §77.
  - §5 D10 reframing — model clarification + error wording; locked in §78.
  - §6 UX items — U7 + U8 shipped as v2.1-patches; both locked here. U9 documentation-only — locked in §81.
  - §7 sequence — v2.1-patches first (shipped), then v2b (this addendum).
  - §8 architect Q&A F, G, H, I, K — all five answered with the recommended option; locked across §§76–78.
- **External pattern verification:** No external review (Gemini/ChatGPT) was solicited for this addendum because the changes are structured extensions of locked decisions rather than new architecture. The next external-review checkpoint is D7 (multi-word strings) per v2a §72.
- **Filename:** `inscript_addendum_v2b_composition_returns.md` — domain `inscript` (provisional, pre-vault), class `addendum`, version `v2b` (second addendum in the v2 series, following v2a), subtitle `composition_returns`. Naming pattern matches v1a–v1d/v2a.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE COMPOSITION RETURNS AND GENERALIZED FIELD ACCESS ADDENDUM v2b*

*May 12, 2026*

*v2a opened the reuse story with `keep` — a verb that doesn't mutate the list it operates on.*
*v2b closes the reuse story's first chapter — compositions wrapping `keep` now return their value, and field access works wherever values flow.*
*The vocabulary stays at 31 reserved words. The clarity budget stays intact.*
*The next chapter is multi-word strings (D7), which warrants its own checkpoint.*
