# Gunray for Barn bug finding

## Goal

Use relevant research to improve Gunray's contribution to Barn correctness testing and deliver the change in a Gunray pull request.

## State

The runnable example emits five managed test cases and a prediction record from 1,800 graphs and 3,780 valid reorder and definition combinations. Regeneration with a different hash seed produced identical files. The focused Gunray pytest passed.

Stock Toast and current Barn passed capability admission and all five cases. The receipt inventories each had five successful MOO observations matching Gunray's expected triples. Pre-fix Barn passed admission and three cases. In both discriminating cases it returned `[node_0, node_0, node_0]` where Gunray expected `[node_0, node_1, node_1]`. All five pre-fix observations matched the breadth-first model. Raw receipts, commands, and JUnit output are in Debian WSL at `/tmp/gunray-parent-order.5QnAHp5K/evidence`.

## Decisions and why

*Korat*, §3.1–3.2, p. 126, and §4.1–4.2, pp. 128–129, describes enumerating a finite input space against preconditions and checking each retained input with a postcondition. Use its finite-domain design for candidate generation. *Metamorphic Coverage*, §4, pp. 5–6, describes code locations exercised by exactly one arm. It motivates measuring the coverage of the new pairs later. Barn's managed runner writes per-session JUnit and observations and has no per-arm coverage input. A future coverage experiment would require independent per-arm profiles from the same Barn build.

- [Korat](https://mir.cs.illinois.edu/marinov/publications/BoyapatiETAL02Korat.pdf)
- [Metamorphic Coverage](https://arxiv.org/abs/2508.16307)

## Surprises

Barn PR #1194 already compares paired observations and loads external Gunray programs. Its `parent_order.py:71` crosses four authored shapes with order reversal and call mode. `vm_cases.py:45` tests warm and cold dispatch across definition rename and restore. `inherited_pass.py:14` changes a single parent during an active call. A remaining case family is reordering a non-leaf object's parent list while descendant dispatch is warm, then comparing with a fresh graph of the same final order. The production operation is `chparents()`, registered and implemented in Barn's `builtins/objects_hierarchy.go:250`. The predicted winner follows the depth-first order in `spec/objects.md:91`.

## Plan

1. Add one runnable Gunray example under `examples/` that emits a managed MOO suite and deterministic prediction records. Enumerate topologically labelled graphs of four and five objects with zero, one, or two distinct ordered parents per node. Restrict the example to two competing definitions of a harmless marker verb and reordering one node's two parents. Those sizes yield 100 and 1,700 labelled graphs before additional filters. Retain case identity in the fact rows.
2. Use Gunray's existing `evaluate_program_file` and a Datalog model for parent-position-path order. Derive the initial and final winner from the generated graph facts. Select meaningful pairs where the swap changes the predicted winner, and keep an unchanged-winner control. Compare a cold graph created in final order with the same graph warmed in initial order and then reordered. Include a small comparison with a breadth-first rule as the known historical control. Keep the executable example and its source citations together.
3. Verify deterministic generation, the historical discriminator, a fresh-versus-warm reorder case beyond Barn PR #1194's matrix, and the unchanged-winner control. Feed generated cases into Barn's existing managed runner with capability admission on stock Toast and current Barn. Keep the raw observations and separate discrepancies from setup failures. Use Gunray PR CI for lint, formatting, typing and conformance. Open the Gunray PR and stop with it open.

## Next step

Open the Gunray PR, verify its CI, and leave it open.
