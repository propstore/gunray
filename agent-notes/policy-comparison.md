# Compare Gunray marking policies

## Goal

Implement the bounded application of Hellerstein’s determination provenance and open a PR. Given one theory and ground literal, report the policies that yield each observed answer.

## State

The dispatcher method and README example are in place. The Antoniou fixture now checks the grouped answer for `q`. That conclusion depends on accepting `p`, which ambiguity propagation blocks by considering opposition from supported premises. The focused test file passed on Windows with the committed lockfile. The repository had no open PR when this work began.

## Decisions and why

- Add `GunrayEvaluator.compare_marking_policies` as a Python API. Evaluate each distinct selected marking policy through the existing dispatcher, share the CLI's answer lookup, and group by the observed answer. A single group means the policies agree. Require at least one policy so agreement always has a defined scope.
- Snapshot the facts once before the first evaluation. `DefeasibleTheory.facts` accepts iterable rows, including one-shot iterators. All policies need the same rows.
- Use the set of policies yielding each answer as the support described by Hellerstein, [Definition 3.2, p. 6](https://arxiv.org/pdf/2606.10270v1#page=6). The selected policies are the entire comparison. A policy error fails the comparison, and other evaluation settings use the dispatcher defaults.
- Keep evaluation semantics inside each existing engine. In the paper’s [Appendix F.3, p. 26](https://arxiv.org/pdf/2606.10270v1#page=26), `d` appears in every stable model but is undefined under the well-founded alternating fixpoint. The policy comparison needs no stable-model or well-founded evaluator.

## Surprises

The CLI already has a four-valued lookup over model sections, including its `UNKNOWN` fallback for omitted rows. Reuse it so both entry points give the same projection answer for the same evaluated model.

The workstation’s user-level `uv` configuration sets `exclude-newer`, which triggers a lock check against a different resolution policy. The focused run used `uv --no-config run --locked --extra dev pytest tests/test_antoniou_ambiguity_policy.py -q` to verify the committed dependency set for this checkout.

## Next step

Publish the change and verify the PR checks.
