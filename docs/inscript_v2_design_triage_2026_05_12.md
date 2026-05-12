# Inscript Programming Language — v2 Design Triage

**Re-tiering and dependency analysis of the eight v2-design items surfaced by the v1 dogfooding pass.**

**Status:** LOGGED — RECOMMENDATIONS FOR ARCHITECT
**Date:** May 12, 2026
**Author:** Rob Thomas / R. Michael Thomas (architect) and Claude (builder, drafting)
**Document type:** Triage — re-tiers the v2-design items from the gap inventory by dependency, blast radius, and spec cost. Identifies design questions that need the architect's decision before code is written. Does not lock any spec change.
**Relationship to prior documents:** Takes as input the v2-design table in `inscript_gap_inventory_2026_05_12_v1_dogfooding.md` (May 12, 2026). Operates within the locked v1 specification (inception checkpoint v1, addenda v1a/v1b/v1c/v1d). Does not modify any locked decision.

---

## How to Read This Document

- §1 frames what triage means in this context.
- §2 is the re-tiered table — the headline finding is that two items (D5, D6) are smaller than v2-design and can ship as v1.1 patches.
- §3–§5 do per-item analysis on the items requiring architectural decisions (D2, D4, D7).
- §6 proposes a sequence.
- §7 enumerates the open design questions for the architect.
- §8 is the resume prompt.

---

## §1 — What "Triage" Means Here

The gap inventory categorized eight items as v2-design. *v2-design* is a coarse bucket — it means "requires spec work" but does not distinguish *how much* spec work, *which items block which*, or *which can ship without a new locked decision*. Triage refines this:

- Some items labeled v2-design are actually solvable inside the v1 codebase with no spec change (renderer improvements, error-message rewording). Those promote to **v1.1-patch**.
- Some items collapse into others (e.g., D3's symptom dissolves if D2 is resolved).
- Some items require a *small* spec addition (a single new connective meaning, a single new verb); others require a *dedicated checkpoint* of their own.

The output of this triage is a recommended sequence, not a locked decision. Each open design question (§7) belongs to the architect.

---

## §2 — Re-Tiered Table

| ID | Original tier | **Triaged tier** | Why this tier | Blocks / blocked by |
|---|---|---|---|---|
| D5 | v2-design | **v1.1-patch** | Error-message change only. Detect `<comp-name> from ...` and emit a v1-specific message. The deferral is already locked (v1b §41). | — |
| D6 | v2-design | **v1.1-patch** | Renderer-only. Keep the descriptor token in the AST and emit it in `canonical_render`. v1b §36 says descriptors are "decorative" (ignored for *semantics*), not "stripped from *rendering*." | — |
| D1 | v2-design | **v2 — small spec addition** | Add a fifth meaning for `and`: inside a `show` clause, `and` between unknowns = list of fields. The four existing meanings in §21 do not claim this slot. | — |
| D2 | v2-design | **v2 — structural** | The single biggest quality-of-life win for the language. Two design paths (§3). | Blocks D3. May want to coordinate with D4 (records). |
| D3 | v2-design | **resolved by D2** | The "destructive composition silently no-ops" symptom dissolves when filter is non-destructive. No independent work. | D2 |
| D4 | v2-design | **v2 — design choice** | Cheap to implement once the form is chosen. The choice is the work. | May want to know D7's quoting decision before locking. |
| D7 | v2-design | **v2 — dedicated checkpoint** | Multi-word strings are the single biggest open semantic question. Touches lexer, parser, the prose-as-syntax invariant, the reserved-word list, and domain packs. | — |
| D8 | v2-design | **defer** | Bundle with "external data sources" already in the v2-deferral table (§25). The 30-item `and` chain worked; the workaround is fine for the v1 target domains. | External data sources |

**Headline finding:** Of the eight items originally tagged v2-design, only six actually require spec work. Of those six, only three (D2, D4, D7) require architectural decisions; the rest (D1, D3, D5+D6 as patches) are implementation choices once the structural questions are resolved.

---

## §3 — D2 Is the Structural Priority

D2 (destructive `filter` makes lists single-use) showed up in three places during dogfooding: Program 2 forced a 30-item re-type to run sequential probes, Program 3 demonstrated that compositions wrapping a destructive filter silently no-op on the second call, and Program 4 required four full list-rebuild statements to test compound conditions. It is the most-recurring quality-of-life gap in the inventory.

Two design paths are viable:

### Path A — Add a non-destructive verb (recommended)

Keep `filter` destructive (v1d §66 explicitly locked it, and the in-place semantics matches business-rules intuition: "filter the orders" means "the orders are now filtered"). Add a new verb — provisionally `keep`, `select`, or `narrow` — that produces a new collection without modifying the source.

```
keep the orders where total is above 50    # new collection, orders unchanged
filter the orders where total is above 50  # orders modified in place
```

**Cost:**
- One new verb (vocabulary count: 7 → 8). Must pass the word salad test (§20).
- One signature (target + condition + output name? auto-named? this is itself a sub-decision).
- One analyzer rule (no homogeneity-of-mutation concerns since output is fresh).
- Compositions wrapping `keep` are reusable on the same data; D3 dissolves automatically.

**Risk:** Low. New vocabulary is the language's intended scaling mechanism (§19 Mechanism 1 — domain packs — and Mechanism 3 — named compositions). Adding one core verb is small relative to the base vocabulary's stability budget.

**Sub-decision:** How does `keep` name its output? Three options:
- Anonymous (auto-show only, must `remember ... from keep ...` to capture).
- Explicit (`keep the orders where total is above 50 called big-orders`).
- Mirror-named (`keep the orders ...` produces `orders-kept`? `kept-orders`? This is the noisiest option and probably wrong).

The first option is the simplest and integrates with the existing `remember ... from <verb phrase>` recursive-descent machinery (§43). The second adds a new `called` position to a verb that already has a `where` clause; not unprecedented but worth a separate look.

### Path B — Snapshot via `from`

Allow `filter the docs from doc-backup where ...` — filter operates on a copy of `doc-backup`, results stored in `docs`. Integrates with the existing `from` disambiguation table.

```
remember the copy called doc-backup from docs
filter the docs from doc-backup where total is above 50   # re-uses doc-backup each time
```

**Cost:**
- A fourth `from` meaning. The §44 disambiguation table currently has three; a fourth makes the ruleset harder to teach.
- Filter's signature gains an optional slot.
- No new vocabulary.

**Risk:** Medium. `from` is already the most-overloaded word in the language (range start, result capture by verb, simple reference by name). Adding a fourth meaning concentrates complexity in a single word.

### Recommendation

**Path A (`keep`).** Three reasons:

1. **Concept-layer alignment (§10).** `keep` is itself a meaningful concept in the business-rules domain — "keep the rows that match." Adding it to the base vocabulary is in keeping with the language's "name what people are trying to do" principle.
2. **Disambiguation hygiene.** Path B concentrates complexity in `from`. Path A distributes it: a new verb has a clean signature with no context-dependent meanings.
3. **Filter keeps its word-salad-tested role.** `filter the orders` reads as "the orders are now filtered" — destructive intuition. `keep` reads as "the matching ones are kept somewhere new" — non-destructive intuition. The two verbs name two genuinely different operations.

Path B is not wrong — it is just costlier on the language's clarity budget.

---

## §4 — D4 (Field Access for Single Records) — Pick a Form

Given `remember an order called order1 with total as 75 and status as active`, v1 has no way to display *one field* of `order1`. The workaround is to wrap the record in a list and iterate. Three candidate forms have different costs:

| Form | Reads as | Cost |
|---|---|---|
| `show total of order1` | natural English | New connective `of`. Reserved-word list: 29 → 30. Disambiguation rule: when next-token after a field-name is `of` + name → field-access. |
| `show order1's total` | natural English | New lexer token (apostrophe-s). Breaks the "split on whitespace" rule (v1c §46 invariant: tokens are whitespace-separated). |
| `show total from order1` | acceptable English | Fourth `from` meaning. Compounds the §43 / §44 / D5 complexity in the most-overloaded word in the language. |

**Recommendation: `of`.** New vocabulary (one reserved word) is cheaper than either a new lexer token or a fourth disambiguation rule on `from`. The word salad test passes: `show total of order1` is what an English speaker would write.

**Interaction with D7.** If D7 adopts quoting for multi-word strings, `show "total" of order1` and `show total of order1` may need to be the same (or deliberately different). Worth deciding D7's direction before locking D4.

---

## §5 — D7 (Multi-Word Strings) Deserves Its Own Checkpoint

Of all the v2-design items, D7 is the one that touches the most spec surfaces:

- **Lexer:** the whitespace-splitting rule (v1c §22, §46) is foundational. Multi-word strings require either a quote mechanism (new lexer state) or a multi-word phrase registry (lookahead beyond one token, beyond what v1c §51 specifies).
- **Parser:** value position currently expects single tokens. Multi-token values change the slot-filling shape.
- **Prose-as-syntax invariant** (v7.5g §13): "valid inscriptions are readable as English prose." Does `"in progress"` count as prose? Does `in-progress`?
- **Reserved-word list** (v1a §29 + v1c §47): multi-word phrases could collide with reserved phrases like `equal to`.
- **Domain packs** (§19 Mechanism 1): each pack adds 10–15 terms. If healthcare introduces `blood pressure` as a multi-word concept, the lexer's phrase registry must reload per session.

Three approaches each have a different "soul":

| Approach | Example | Soul / tradeoff |
|---|---|---|
| **Quoting** | `remember an order called order1 with status as "in progress"` | Adds syntax marks. Cleanest mechanically. Noisiest visually for non-programmers — quote marks are the closest thing to "programming syntax" the language would have. |
| **Hyphenation** | `with status as in-progress` | Already works in v1. Punts on the prose question by changing the prose. Adopted ad-hoc in dogfooding for `gap-inventory`, `find-large`, `nums-copy` — comfortable for hyphen-aware English. |
| **Multi-word phrase spans** | `with status as in progress` | Lexer accumulates known multi-word phrases from a registry. Reads as natural prose. Requires phrase registry, conflict resolution with single words, stable definition of "known," and domain-pack-aware reloading. |

This is not a one-PR question. **Recommendation: dedicated v2 checkpoint** with the same external-review pattern (Gemini + ChatGPT) that validated v1a–v1d, with domain-pack collision as a first-class question.

---

## §6 — Recommended Sequence

| Step | Items | Effort | Output |
|---|---|---|---|
| 1 | **v1.1 patches: D5 + D6** | Hours, no spec change | Better `from`-chaining error; descriptor preserved in canonical rendering. Commit-as-you-go. |
| 2 | **v2 small additions: D1 + D2 + D4** | One spec addendum + implementation | Pick D2 path (recommended: `keep`). Lock D1 (fifth `and` meaning). Lock D4 form (recommended: `of`). One addendum captures all three. D3 dissolves as a side effect. |
| 3 | **v2 dedicated checkpoint: D7** | One checkpoint + external review | Multi-word strings approach decision. New reserved-word list. Domain-pack collision rules. |
| 4 | **Defer D8** | — | Bundle with external data sources in a future v2 spec session. |

Steps 1 and 2 are independent. Step 3 may want to land before D4 is fully locked if quoting changes how `of` should work.

---

## §7 — Open Design Questions for the Architect

These need a decision before any code is written:

| Q | Question | My recommendation | Cost of getting it wrong |
|---|---|---|---|
| **A** | **D2 path.** New verb (`keep` / `select` / `narrow`) or `from` snapshot? | **New verb** — recommend `keep`. | If wrong: a verb gets added that doesn't pass the word salad test, or `from` accumulates a fourth meaning that frustrates teaching. |
| **B** | **D2 sub-decision.** How does the new verb name its output — anonymous (auto-show + `remember ... from`), explicit `called`, or implicit-name from target? | **Anonymous** — re-use the §43 `remember ... from <verb phrase>` machinery. | Adding `called` to filter-shaped verbs sets a precedent that the architect should be aware of before locking. |
| **C** | **D1 mechanism.** Fifth `and` meaning in `show` clause, or a different construct like `each ... show with words and class`? | **Fifth `and` meaning** — smaller, no new connective. | If wrong: an extra connective gets introduced that subsumes existing meaning. |
| **D** | **D4 form.** `of` / `'s` / `from`? | **`of`** — one new reserved word, no lexer changes, no `from` overload. | If wrong: lexer rule changes (apostrophe-s) or `from` complexity grows. |
| **E** | **D7 approach.** Quoting / hyphenation / multi-word phrase spans? | **Defer to dedicated checkpoint.** Each approach has serious tradeoffs. | If wrong: the foundational lexer rule changes, or domain packs become collision-prone, or the prose-as-syntax invariant softens. |

The architect's decisions on A–D could be made in a single short session. E requires a checkpoint of its own.

---

## §8 — Resume Prompt (v2 Design Triage)

*We are resuming from the Inscript v2 Design Triage (May 12, 2026), which re-tiers the eight v2-design items from the dogfooding gap inventory (same date). **Two items (D5, D6) demote to v1.1-patch — small renderer/error-message changes with no spec impact.** **Three items (D1, D2, D4) form a single v2 spec addendum** once the architect picks paths: recommended is the fifth `and` meaning in `show` clauses (D1), a new non-destructive `keep` verb (D2, dissolving D3), and the new `of` connective for record field access (D4). **One item (D7 — multi-word strings) needs its own checkpoint** with external review, because it touches the lexer's whitespace rule, the prose-as-syntax invariant, the reserved-word list, and domain-pack collision rules. **One item (D8) defers** to whenever external data sources are taken up. Five open design questions (A–E in §7) need architect decisions; A–D could be resolved in one session, E requires a checkpoint of its own. The next concrete steps are: (1) ship D5 + D6 as v1.1 patches whenever convenient; (2) Rob decides A–D and Claude drafts the addendum; (3) schedule the D7 checkpoint.*

---

## Provenance Note

This triage was produced from:

- **`inscript_gap_inventory_2026_05_12_v1_dogfooding.md`** (May 12, 2026): All eight v2-design items (D1–D8) sourced from this document.
- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026): Verb signatures (§17), `and`/`or` four-meaning table (§21), vocabulary scaling mechanisms (§19), concept-layer principle (§10), word salad test (§20), open Q9 (composition parameters), v1/v2 deferral table (§25).
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026): Reserved word list (§29), canonical prose rendering (§33).
- **`inscript_addendum_v1b_design_resolutions.md`** (May 11, 2026): Prose descriptors decorative (§36), composition call syntax (§41), `from` disambiguation (§43), complete parser disambiguation ruleset (§44).
- **`inscript_addendum_v1c_implementation_hardening.md`** (May 11, 2026): Whitespace splitting (§46), parser lookahead capability (§51).
- **`inscript_addendum_v1d_build_boundary.md`** (May 11, 2026): In-place filter explicitly locked (§66), single-token strings explicitly locked (§61).
- **`mobius_paradigm_checkpoint_v7_5g_inscript_resolution.md`**: Prose-as-syntax invariant (§13).
- **Dogfooding programs** (`examples/dogfood_*.insc`, May 12, 2026): Practical evidence for each gap's blast radius, especially Program 2 (30-item rebuild for D2), Program 3 (composition no-op for D3), and Program 4 (four full rebuilds for compound-condition probes).
- **Filename:** `inscript_v2_design_triage_2026_05_12.md` — domain `inscript`, class informally `triage`, date suffix matching the gap inventory it derives from. Verified against the naming pattern of prior `inscript_*` documents in `docs/`.

---

*END OF INSCRIPT v2 DESIGN TRIAGE*

*May 12, 2026*

*Eight items labeled v2-design. Two were smaller than that label. One is larger. The rest fit one addendum if the architect picks four paths.*
*Triage is not the spec. It is the map that says where the spec needs to be written.*
