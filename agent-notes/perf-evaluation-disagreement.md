# Evaluation-local disagreement checks

**Goal** Speed up the blocking-policy repro with 6, 8 and 10 arguments per side, preserve model sections, check in the benchmark, and open a draft PR after verification.

**State** The argument builder and dialectical trees share the closure of Pi and one evaluation-local cache keyed by unordered ground literal pairs. Contradiction checks look up shared argument tuples for configured predicate pairs. The pytest benchmark asserts the full model sections, and a separate regression checks that each evaluation rebuilds its cache.

**Decisions and why** Keep standalone disagreement calls stateless. Public tree callers can supply grounded strict inputs as before, and each call builds its own cache. Use the existing pytest performance module for the repro.

**Surprises** The parser adds complementary predicate pairs to its conflict set, so the repro reaches the explicit-conflict scan even with no configured conflicts. The checked-in benchmark measured 1.401173s, 5.735451s and 18.778627s before, and 0.076801s, 0.209302s and 0.428174s after. The complete model sections assertions passed at every size on both revisions.

**Verification** Ruff lint, Ruff format and Pyright passed. The full local suite is running with the same evaluator as CI.

**Next step** Publish the draft PR and verify the full suite and PR CI.
