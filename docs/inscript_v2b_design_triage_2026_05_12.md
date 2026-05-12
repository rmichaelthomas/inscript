# Inscript Programming Language — v2b Design Triage

**Re-tiering and dependency analysis of the six new gaps surfaced by the v2a dogfooding pass.**

**Status:** LOGGED — RECOMMENDATIONS FOR ARCHITECT
**Date:** May 12, 2026
**Author:** Rob Thomas / R. Michael Thomas (architect) and Claude (builder, drafting)
**Document type:** Triage — re-tiers the six gaps (D9, D10, D11, U7, U8, U9) from the v2a dogfooding inventory by dependency, blast radius, and spec cost. Identifies design questions that need the architect's decision before code is written. Does not lock any spec change.
**Relationship to prior documents:** Takes as input the v2a-design table in `inscript_gap_inventory_2026_05_12_v2a_dogfooding.md` (May 12, 2026). Operates within the locked specification (inception checkpoint v1 + addenda v1a/v1b/v1c/v1d/v2a). Sibling to the earlier `inscript_v2_design_triage_2026_05_12.md` (May 12, 2026), which triaged D1–D8 and fed v2a. This one feeds the next addendum (provisionally v2b).

---

## How to Read This Document

- §1 frames what triage means here, and what changed from the v2a triage.
- §2 is the re-tiered table — the headline finding is that **D10 isn't actually structural** (it's a category mismatch with an unhelpful error), and **U7/U8 can ship as v2.1-patches** without spec work.
- §3 covers **D9** (composition return values) — the structural priority. Two paths with explicit cost/risk.
- §4 covers **D11** (generalize `of` to value positions) — small parser change, bundles naturally with D9.
- §5 covers **D10** (per-record `keep` inside `each`) — reframes as model clarification + error improvement.
- §6 covers the UX items (U7, U8, U9) — three small fixes, one of them a doc-only note.
- §7 proposes a sequence.
- §8 enumerates the open design questions for the architect.

---

## §1 — What Changed from the v2 Design Triage

The first triage (`inscript_v2_design_triage_2026_05_12.md`) sorted D1–D8 from the v1 dogfooding. The architect picked paths, and `inscript_addendum_v2a_dogfooding_resolutions.md` shipped them. The v1 UX polish (U1–U5) followed in a separate patch round.

A second dogfooding pass against v2a + the UX polish surfaced six new items:

- Three v2-design gaps: D9 (composition return values), D10 (per-record `keep` inside `each`), D11 (`of` outside `show`).
- Three UX gaps: U7 (duplicate fields in multi-field `each show`), U8 (`of`-on-list error suggests no alternative), U9 (operation-sequencing emits both outputs).

On closer triage, two of the six **demote**: D10 is a category-mismatch artifact rather than a missing feature, and U9 is a documentation question rather than a code change. Two more (U7, U8) are pure patches. The remaining two (D9, D11) form a tightly coupled v2b addendum about *value flow* — what compositions return, and where field-access expressions can appear.

---

## §2 — Re-Tiered Table

| ID | Original tier | **Triaged tier** | Why this tier | Blocks / blocked by |
|---|---|---|---|---|
| D9 | v2-design | **v2 — structural** | Biggest single win for the language's reuse story. Tied to Q9 (composition parameters). Two design paths (§3). | Compounds naturally with D11 (both about value flow). |
| D11 | v2-design | **v2 — small spec addition** | Generalize `of` to value positions. Parser change is local; disambiguation rule is simple (after a NAME, `of` → field-access value-expression). No new vocabulary; `of` is already reserved. | Bundles with D9 in one addendum. |
| D10 | v2-design | **spec clarification + error improvement** | Not a missing feature — `keep` is a list operation and `each` iterates records; the constructs don't compose. The user's intent ("decide each item conditionally") is already expressible via list-level `keep ... where`. The "gap" is really an unhelpful error and an unstated model assumption. | None. |
| U7 | UX | **v2.1-patch** | Analyzer-level check. Detect repeats in `ShowNode.extra_fields` and emit a semantic error. ~10 lines. | None. |
| U8 | UX | **v2.1-patch** | Pure error-wording improvement: when `of`-on-list fires, suggest the `each` alternative. ~5 lines. | None. |
| U9 | UX | **documentation note** | Operation-sequencing emits both outputs because each verb in a sequence runs to completion (v1d §56 stepwise execution). Suppressing auto-show on the first verb would be a behavior change. The right fix is documentation in v2a §67. | None. |

**Headline finding:** Of the six items originally tagged as v2a-dogfooding gaps, only **two** require architectural decisions (D9 and D11). Three (D10, U7, U8) are small implementation/wording fixes. One (U9) is a documentation note.

---

## §3 — D9: Composition Return Values

`remember the X from <comp-name>` currently errors: *"Composition calls can't be used as a value in this version."* The interpreter's `_evaluate_expression` explicitly rejects `CompositionCallNode` in value position. This is pre-existing v1 behavior — but `keep` (v2a §67) made it newly painful, because `keep` is the natural thing to wrap in a composition for reuse. The dogfooding workflow "define a reusable filter, capture its result" collapses to "redefine the body verbatim each time."

Two design paths.

### Path A — Implicit return: the value of the composition's last operation (recommended)

`gather`, `combine`, and `count` already have an auto-return pattern — each produces a value that can be used by `remember ... from <verb-phrase>` via v1b §43's recursive descent. Apply the same intuition to compositions:

```
remember how to find-major: keep the docs where words is above 7000
remember the heavy called heavy from find-major
```

`find-major` returns whatever its body's last operation returns — in this case, the matched list from `keep`. The interpreter wires `_evaluate_expression` to execute the composition body and use the last operation's output value.

**Cost:**
- One interpreter change — `_evaluate_expression` handles `CompositionCallNode` by executing the body and returning the last op's value.
- One analyzer change — the value-capture path needs to know the composition's body has a defined return type. Could be lazy (check at call time).
- No vocabulary changes. No new spec section beyond locking the return rule.

**Risk:** Low. The pattern already exists for verb phrases. Adding it for composition calls removes one rejection rule; doesn't introduce new ambiguity.

**Sub-decisions** needed:

1. **Multi-statement bodies.** When a composition body is a `SequenceNode` (operations joined by `and`), the last op's value is returned. Other ops' side effects still occur (consistent with v1d §56 stepwise).
2. **Void-result verbs.** `show`, `filter`, `each`, `remember` are side-effect-only — they don't produce a captured value. A composition ending in one of these has no return value. Two options:
   - (a) Error at the call site: *"Composition '<name>' doesn't return a value — its last operation is '<verb>', which only has side effects."*
   - (b) Return an "empty result" silently, treated as a void value in value position.
   - **Recommendation: (a) error.** Silent empty returns hide user mistakes and violate v1c §52 (deterministic interpretation only). The error message tells the user how to fix it.
3. **`each ... show` inside a composition.** Produces output lines, not a value. Treated as void-result (errors per option 2(a)).
4. **Nested composition calls.** If `find-major` calls `find-large` which calls `keep`, the chain unwinds through `_evaluate_expression`. No special rule needed.

### Path B — Explicit return marker

Add a new connective such as `give` or `return`:

```
remember how to find-major: keep the docs where words is above 7000 give the result
```

**Cost:**
- One new connective (reserved-word count: 31 → 32).
- New parser rule for the `give` clause.
- Discriminator at composition definition between explicit-return and side-effect-only.

**Risk:** Medium. Adds vocabulary for something the existing auto-return pattern already covers. The vocabulary tray grows for a marginal expressiveness gain.

### Recommendation

**Path A.** Two reasons:

1. **Pattern consistency.** `gather`, `combine`, `count` are already auto-returning via v1b §43's recursive descent. Compositions becoming the fourth member of this family is the smallest spec addition consistent with what exists.
2. **No new vocabulary.** The vocabulary budget is the language's clarity budget (inception §19, §20). Path B spends a reserved word on a distinction the user wouldn't articulate without prompting.

Path B is not wrong — it's just costlier on the language's clarity budget for a feature most users would expect to "just work."

---

## §4 — D11: Generalize `of` to Value Positions

v2a §68 scoped `of` to `show <field> of <record>`. The dogfooding pass found natural prose expressions that v2a doesn't accept:

```
keep the docs where words is above words of doc-1
remember a copy called holder with total of order1
filter the orders where total is above total of baseline-order
```

Each reads as English. Each fails to parse because `of` is only consumed in `_parse_show`.

**The generalization:** `<field> of <record>` is a valid value-expression anywhere a value or field reference is expected. Parser rule: after consuming a NAME (UNKNOWN token) in a value or field-reference position, if the next token is `of`, consume `of` + the next NAME, and produce a field-access AST node.

**Cost:**
- Extract the existing `<field> of <record>` consumption logic into a `_consume_value_with_optional_of` helper.
- Use it in: `_parse_value`, `_parse_simple_condition` (field-reference position), `_parse_remember_with` (value position).
- New AST node `FieldAccess(field: str, record_name: str)` (or extend an existing node — the v2a `ShowNode.record_name` mechanism is one option).
- Analyzer/interpreter learn to resolve a field-access expression: look up the record, verify the field exists, return the value.

**Risk:** Low. `of` is already reserved (v2a §73). The disambiguation rule is unambiguous (after a NAME, `of` always means field access — it has no other meaning).

**Sub-decision needed.**

**J — Should `of` chain?** `field-a of field-b of record1` is currently undefined. v2a §68 already leaves this open. Two options:

- (a) Single-level only: parser sees the first `of`, consumes one record name, stops. Chaining is rejected at parse time.
- (b) Right-associative chaining: `field-a of field-b of record1` means `field-a of (field-b of record1)`. Requires nested records, which aren't an established v2 data shape.

**Recommendation: (a) single-level.** Nested records aren't a v1/v2 data type — records are flat field→value maps. Chained `of` belongs in the same future session that defines nested records. Until then, single-level keeps the spec deterministic and avoids over-promising.

---

## §5 — D10: Per-Record `keep` Inside `each` — Reframe as Clarification

`each the docs keep where words is above 9000` errors at parse: *"I expected a target after 'keep', but 'where' is a connective."* The parser is correct — `keep` requires an explicit target name, and inside an `each` body the "current item" has no name.

On closer look, **this isn't a missing feature**:

- `keep` is a list operation (target = a list, condition = a where-clause that runs against each item).
- `each` iterates a list, binding one item at a time.
- "Inside `each`, do `keep`" is a category error — there's no list to operate on per iteration.

The user's intent ("decide whether to keep each item conditionally") is **already expressible** via list-level filtering:

```
each the docs keep where words is above 9000     # rejected — category error
keep the docs where words is above 9000          # the intended workflow
```

The v1 target domains (business rules, compliance, data filtering) are list-shaped, not per-record-shaped. Per-record decisions belong in `keep`'s `where` clause.

**Two small fixes** (no spec change):

1. **Update the parse error.** Detect the specific case `each <list> keep` and emit a guidance error rather than the generic parse error: *"`keep` is a list operation — it can't appear inside `each`. To keep only some items, use `keep <list> where <condition>` directly."*
2. **Document the model in v2b §X.** A single paragraph noting that `keep`/`filter` are list operations and `each` is for display/iteration; per-item decision logic lives in the `where` clause of a list operation.

This closes D10 without adding language surface area.

**If the architect believes per-item decision logic is genuinely a missing capability** — e.g., a future business-rules use case where decisions need access to per-item context the `where` clause can't easily express — then a per-item `do` construct (or similar) could be a separate v2-design item. For now, the v2a dogfooding's specific case (`keep` inside `each`) is a clarification, not a feature.

---

## §6 — UX Items: U7, U8, U9

**U7 — Duplicate fields in multi-field `each show` silently allowed.**

`each the docs show domain and class and class` produces `domain: X, class: Y, class: Y`. v2a §69 doesn't lock either acceptance or rejection. Silent acceptance lets typos through.

**Fix:** v2.1-patch. In the parser or semantic analyzer, detect repeats in `ShowNode.extra_fields` and emit a semantic error: *"You listed '<field>' twice in this show. Did you mean another field?"* — consistent with v1c §52 (deterministic interpretation only). ~10 lines.

**U8 — `of`-on-list error doesn't suggest `each`.**

Current: *"'of' needs a record. 'docs' is a list of records."* User intent is almost always "show me each doc's words." Extend the message:

*"'of' needs a single record. 'docs' is a list of records — did you mean: each the docs show <field>?"*

**Fix:** v2.1-patch. ~5 lines in `_check_show`.

**U9 — Operation-sequencing emits both outputs.**

`keep ... and show docs` runs both verbs (v1d §56 stepwise), and each emits its output. The user might want either one alone — they can use `remember ... from keep ...` to silence `keep`'s auto-show, but there's no in-line silencer.

This is a documentation question, not a behavior bug. Suppressing the first verb's auto-show on sequencing would be a behavior change that interacts with v1d §56's stepwise locking.

**Fix:** Documentation note in v2a §67 (or v2b §X if v2b ships): *"`keep` always auto-shows its matches unless its result is captured via `remember ... from keep ...`. In an operation sequence (`keep ... and <next>`), `keep` runs first, displays its matches, and then the next operation runs and displays its output. To suppress `keep`'s display, capture into a name first."*

---

## §7 — Recommended Sequence

| Step | Items | Effort | Output |
|---|---|---|---|
| 1 | **v2.1-patches: U7 + U8 + D10 error wording** | Hours, no spec change | Duplicate-field rejection, `of`-on-list improved error, `each ... keep` improved error. One commit. |
| 2 | **v2b spec addendum: D9 + D11 + D10 model clarification** | One addendum + implementation | Composition return values (Path A) + generalized `of` (single-level) + a paragraph clarifying the list/iteration model. Both code changes about *value flow*. |
| 3 | **Documentation: U9 note** | Minutes | Add to v2b §X or v2a §67. No code change. |

Steps 1 and 3 are small. Step 2 is the substantive next chapter — and it's the natural next chapter of the reuse story v2a opened.

---

## §8 — Open Design Questions for the Architect

These need a decision before any code is written:

| Q | Question | My recommendation | Cost of getting it wrong |
|---|---|---|---|
| **F** | **D9 path.** Implicit-return (Path A) or explicit-return marker (Path B)? | **Path A** — implicit return of the last operation's value. Matches the auto-return intuition of `gather`/`combine`/`count`. | If wrong: adds new vocabulary (`give`/`return`) for something the existing pattern covers. Adding vocabulary is harder to remove than to add. |
| **G** | **D9 sub-decision.** What happens when a composition's last operation is void-result (`show`, `filter`, `each`, `remember`)? | **Error** at the call site if used in value position. Side effects still occur when called as a statement. | If wrong: silent empty returns mask user errors; violates v1c §52 (deterministic interpretation only). |
| **H** | **D11 scope.** Generalize `of` to all value positions in one step, or take it incrementally? | **Generalize once.** Single parser rule, single disambiguation. Incremental rollout would have ambiguous interaction with the existing `show`-only path. | If wrong: spec churn over multiple addenda for what is structurally one decision. |
| **I** | **D11 sub-decision.** Should `of` chain (`field-a of field-b of record1`)? | **Single-level only.** Nested records aren't a v1/v2 data shape. Chained `of` belongs in the same future session that defines nested records. | If wrong: parser accepts syntax that has no defined semantics; users will write programs that "work" until nested records ship and break the meaning. |
| **K** | **D10 framing.** Clarify the model (list operations only; no per-record decisions) or leave room for a future `each ... do <verb>` construct? | **Clarify the model in v2b.** v1 target domains (business rules, compliance, filtering) are list-shaped. If a per-record-decision use case emerges later, add it as a fresh design item with its own grammar. | If wrong: "per-record do" becomes an open design loop without a clear use case to anchor it. |

F, G, H, I, K could be resolved in a single short session. The bigger architectural decision is F (implicit vs. explicit return) — it shapes how `keep` and compositions compose for the rest of the language's life.

---

## §9 — Resume Prompt (v2b Design Triage)

*We are resuming from the Inscript v2b Design Triage (May 12, 2026), which re-tiers the six new gaps from the v2a dogfooding inventory (same date). **D9 (composition return values) is the structural priority** — it's the next chapter of the reuse story v2a opened with `keep`. Two design paths: implicit-return-of-last-op (Path A, recommended — matches gather/combine/count auto-return) vs. explicit-return marker (Path B — new vocabulary). **D11 (generalize `of` to value positions)** is a small parser change with no new vocabulary; bundles naturally with D9 in one v2b addendum about value flow. **D10 (per-record `keep` inside `each`) reframes as model clarification** — `keep` is a list operation, `each` iterates records, the constructs don't compose; user intent is already expressible via `keep <list> where <condition>`. Just needs a clearer error message + a paragraph of model documentation. **U7 + U8 are v2.1-patches** (~15 lines total). **U9 is a documentation note**, not a code change. Five open design questions (F, G, H, I, K) for the architect; F (D9 path) is the load-bearing one. The next concrete steps: (1) ship U7 + U8 + the D10 error wording as v2.1-patches whenever convenient; (2) Rob decides F–K and Claude drafts the v2b spec addendum (D9 + D11 + D10 model clarification); (3) U9 documentation note lands in the v2b addendum.*

---

## §10 — Provenance Note

This triage was produced from:

- **`inscript_gap_inventory_2026_05_12_v2a_dogfooding.md`** (May 12, 2026): All six gaps (D9–D11, U7–U9) sourced from this document, including both the original first-pass findings and the second-pass observations after the v1 UX polish landed.
- **`inscript_addendum_v2a_dogfooding_resolutions.md`** (May 12, 2026): §67 (`keep` verb), §68 (`of` connective, single-level), §69 (multi-field `each show`, fifth `and` rule), §72 (D7 deferral). D9 is the natural next step after §67; D11 generalizes §68; U7 lives within the rules of §69.
- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026): §10 (concept-layer vocabulary) — referenced in §3's rationale against adding a new connective for Path B. §11 (vocabulary scaling budget) — invoked for the "no new vocabulary" principle. §17 (verb signatures) — `keep` has the signature D9 builds on. §19 (vocabulary scaling architecture) and §20 (word salad test) — the bar Path B fails. §25 (v1/v2 deferral table) including Q9 (composition parameters) — D9 is the natural Q9 resolution.
- **`inscript_addendum_v1b_design_resolutions.md`** (May 11, 2026): §43 (`from` disambiguation, recursive descent) — D9 extends this mechanism to composition calls. §44 (complete disambiguation ruleset) — D11 adds one rule to this table.
- **`inscript_addendum_v1c_implementation_hardening.md`** (May 11, 2026): §52 (deterministic interpretation only) — invoked in §3 sub-decision 2 (error vs. silent empty return) and §6 (U7 duplicate-field rejection).
- **`inscript_addendum_v1d_build_boundary.md`** (May 11, 2026): §56 (stepwise execution) — referenced in §6 (U9 documentation rather than behavior change).
- **`inscript_v2_design_triage_2026_05_12.md`** (May 12, 2026): Sibling triage, format precedent. The v2-design items it triaged (D1–D8) shipped in v2a; this triage continues the same pattern for D9–D11 + UX items.
- **Second-pass dogfood programs** (`examples/dogfood_v2a_14_realistic.insc`, `_15_scale.insc`, `_16_schema_errors.insc`): Practical evidence that the UX polish doesn't surface new gaps and that D9/D10/D11/U7/U8/U9 remain real after the polish.
- **Filename:** `inscript_v2b_design_triage_2026_05_12.md` — domain `inscript`, class informally `triage`, date suffix matching the gap inventory it derives from. Naming pattern follows `inscript_v2_design_triage_2026_05_12.md` (the v2a precursor).

---

*END OF INSCRIPT v2b DESIGN TRIAGE*

*May 12, 2026*

*Six new gaps from v2a dogfooding. Two are structural — both about value flow. Three are small patches. One is a documentation note.*
*The v2b addendum is the next chapter of the reuse story: keep returns; of generalizes; the list/iteration model is named.*
*The vocabulary tray stays at 31 reserved words. The clarity budget stays intact.*
