# Repair Gunray conformance before rebasing PR #2

## Goal

Resolve the conformance failures in a separate PR against `master`. Verify and merge that repair, then rebase and verify PR #2. Leave PR #2 open.

## State

PR #2’s conformance run reported 141 failures: 91 generated mixed cases, 42 generated chains, six generated strict overrides, and two SPINdle contradiction cases. This branch enables the full pinned suite and implements the first three fixes below. The argument-building test file passed. An independent run compared the grounded-head domain from the public DePYsible source, Gunray’s grounding inspection, and each stored result for all 701 generated cases. Every domain agreed. All cases used schematic rules and four were strict-only.

## Decisions and why

- Delete the two local expectation overrides. The pinned SPINdle cases expect both complements to be strictly provable. The existing SPINdle route already produces those results. García’s separate consistency requirement stays in the DeLP path. [Maher and Governatori, proof theory, PDF pp. 2–3](https://cdn.aaai.org/AAAI/1999/AAAI99-044.pdf#page=2)
- Visit grounded strict rules alongside grounded defeasible rules when combining premise supports. The strict rule remains in Π, and the support records only defeasible rules. The same closure, contradiction, minimality, default-negation, and budget checks apply. `defeasible_gen_chain_0001` exercises a strict step after a defeasible step. The focused argument test exercises a strict join of two independent supports. [García and Simari, Definitions 2.5 and 3.1, pp. 100–103](https://doi.org/10.1017/S1471068403001674)
- For the generated DePYsible corpus, select the oracle projection using the pinned suite’s source metadata. Compare the full stored result over the input-derived domain. The model returned to Gunray callers still has its full set of answers. [DePYsible interpreter](https://github.com/stefano-bragaglia/DePYsible/blob/master/src/main/python/depysible/domain/interpretation.py)

## Surprises

DePYsible’s `not_defeasibly` section carries DeLP `Answer.NO`. Maher’s `-∂` represents a different proof condition. The test uses García warrant, with DePYsible’s reporting domain supplied at the conformance boundary.

The focused conformance run passed both SPINdle cases and every generated chain. It found 60 disagreements in generated strict-override and mixed cases under complete row comparison. `defeasible_gen_strict_override_0001` records warrants for both `goal` and `~goal` even though `~goal` is strict. DePYsible’s `Derivation.get_structure` takes the defeasible rules from any derivation, and `Interpreter._get_warrant` marks them without checking whether adding that support contradicts Π. García and Simari, Definition 3.1(2), p. 103 and its discussion on p. 104, rule out the contrary support. Further disagreements require their own verdicts.

The first two CI attempts exposed the import layout in `tests/test_conformance.py` and the element type inferred for the empty frozenset in `arguments.py`. The formatter’s layout is applied and the empty set shares the `GroundDefeasibleRule` element annotation with the nonempty branch.

## Next step

Compare the remaining failed fixtures against the paper and reference implementation. Verify Ruff, Pyright, unit tests, and the full pinned suite on the repair PR. Merge with a merge commit once the checks pass. Preserve the policy-comparison worktree’s local note while rebasing PR #2 and verify its new head after publishing with a lease.
