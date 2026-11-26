# `examples/` — a guided tour

Each script is runnable as `uv run python examples/<name>.py` and
doubles as a self-checking assertion suite (every file ends with
`assert result is Answer.X`). Read them in the order below.

## Tier 1 — Showcase

| Script | What it shows |
| --- | --- |
| [`nixon_diamond.py`](nixon_diamond.py) | Equi-specific defeasible rules leave the query `UNDECIDED`. Shows: Garcia & Simari 2004 Def 5.3 four-valued answer. |
| [`innocent_until_proven_guilty.py`](innocent_until_proven_guilty.py) | Presumption (`innocent -< true`) overridden by evidence and attacked by a blocking defeater. Shows: `presumptions=[...]` + `defeaters=[...]`. |
| [`reviewer_assignment.py`](reviewer_assignment.py) | Multi-axis peer-review COI (coauthor / institution / advisor). An undercutting defeater waives only the institution axis; superiority keeps advisor-COI above the waiver. Shows: defeaters + incomparable disqualifiers — not scalar-reducible. |
| [`access_control_break_glass.py`](access_control_break_glass.py) | Financial authorization where emergency overrides audit hold but is itself overridden by the self-dealing bar, and deliberately cannot trump four-eyes. Shows: partial-order superiority + `UNDECIDED` when policy is silent. |
| [`gdpr_lawful_basis.py`](gdpr_lawful_basis.py) | Two independent lawful-basis paths; withdrawal beats consent via explicit `superiority=[("d2", "d0")]`. Shows: user superiority layered on specificity. |

## Tier 2 — Domain depth

| Script | What it shows |
| --- | --- |
| [`platypus.py`](platypus.py) | Strict rule wins over defeasible default — mammals don't fly, except when they do (no: platypuses still don't). Shows: strict-over-defeasible precedence. |
| [`clinical_drug_safety.py`](clinical_drug_safety.py) | Layered contraindications with explicit superiority. Shows: defeasible clinical reasoning. |
| [`looks_red_under_red_light.py`](looks_red_under_red_light.py) | Pollock's perception defeater: `looks_red` defeasibly supports `red`, but red-light undercuts the perception rule. Shows: undercutting defeaters. |
| [`data_fusion_sources.py`](data_fusion_sources.py) | Conflicting sensor readings resolved by source-preference superiority. Shows: data fusion with trust. |
| [`config_precedence.py`](config_precedence.py) | Site < project < user < flag cascade. Shows: precedence via specificity + superiority. |
| [`explanations_gallery.py`](explanations_gallery.py) | Six canonical cases each rendered with `explain(tree, criterion)`. Shows: prose explanations (F-B). |

## Tier 3 — Engine breadth

| Script | What it shows |
| --- | --- |
| [`git_ancestry.py`](git_ancestry.py) | Recursive ancestor relation via `SemiNaiveEvaluator`. Shows: stratified Datalog. |
| [`klm_config_defaults.py`](klm_config_defaults.py) | KLM rational/lexicographic/relevant closure on propositional defaults. Shows: `ClosureEvaluator`. |
| [`safe_vs_nemo.py`](safe_vs_nemo.py) | Same theory, two negation semantics, different answers. Shows: `NegationSemantics.SAFE` vs `NegationSemantics.NEMO`. |
| [`barn_parent_order.py`](barn_parent_order.py) | Bounded generation of ordered-inheritance cases for Barn and ToastStunt. The [Datalog model](barn_parent_order.gnr) predicts which verb wins before and after a parent-list reorder. |

### Generate ordered-inheritance cases for Barn

```bash
uv run python examples/barn_parent_order.py /path/to/run
```

Gunray evaluates ordered graphs with four or five objects, up to two parents per
object, and two definitions of the same verb. It selects one example per
combination of direct or indirect ancestry and agreement or disagreement with
breadth-first lookup, plus one case where the winner stays the same. The generated
suite calls through the same verb before and after reordering, then compares that
result with a fresh graph that started in the final order.

The command writes `candidate/cases/gunray_parent_reorder.yaml` and
`evidence/predictions.json` beneath the run directory. Use the managed runner
from [Barn's property suite](https://github.com/MongooseMoo/barn/pull/1194)
with `gunray_parent_reorder` as its suite argument. The generator runs without
either engine installed.

The input bound follows Boyapati, Khurshid, and Marinov's approach in
[*Korat*, §3.1, p. 126 and §4, pp. 128–129](https://mir.cs.illinois.edu/marinov/publications/BoyapatiETAL02Korat.pdf).
The model uses the parent order specified in
[Barn's object semantics, §3.3](https://github.com/MongooseMoo/barn/blob/master/spec/objects.md#33-inheritance-resolution).

## Tier 4 — Visuals

| Script | What it shows |
| --- | --- |
| [`mermaid_gallery.py`](mermaid_gallery.py) | Emits `.mmd` files for five dialectical trees via `render_tree_mermaid` (F-C). |
| [`mermaid/*.mmd`](mermaid/) | Rendered Mermaid diagrams: `nixon_diamond`, `innocent_coerced`, `reviewer_waiver_overruled`, `break_glass_vs_four_eyes`, `clinical_aspirin`, `opus`. |
