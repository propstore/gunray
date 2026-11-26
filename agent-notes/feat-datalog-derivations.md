# Datalog derivations

## Goal

Make Gunray explain a derived Datalog tuple using one actual rule application and its matched input rows. Verify the same API with two existing external model families and deliver one Gunray pull request.

## State

The derivation map is allocated only when requested. The generic matcher is the source of matched evidence, including values captured by wildcards. The file evaluation entry point returns the same projected model and a trace over all evaluated relations.

`uv run --frozen --extra dev pytest tests/test_datalog_derivations.py` passed. The public file API reproduced the existing Barn assignment-order and range-write results using their saved input rows. The assignment error led to the injected fault, the throw value, and the preceding reached stages. The range error led to two type facts and the instantiated inequality. Removing the fault yielded the update proof and no error derivation. Setting the replacement type to match yielded the applicability proof and no error derivation. Normal and traced models were equal for all four inputs. The external replay script and raw data are local at `C:/Users/Q/AppData/Local/Temp/gunray-provenance-2a92a400a0ad42ea83a3439f1aaa5213`.

## Decisions and why

Record one witness at first insertion. Its premises were visible to the rule and are already in the input or earlier completed evaluation batches. Store links as tuples for on-demand traversal. The paper's minimum-height guarantee requires updating existing annotations. This diagnostic use needs a valid witness for the reported prediction. See [Zhao, Subotić, and Scholz](https://doi.org/10.1145/3379446), Def. 2.1 and §3.3, pp. 7:7 and 7:16–17.

## Surprises

The existing compiled rule path returns head rows alone, and the binding path loses wildcard columns. Opt-in collection uses the existing generic join path to record the exact matched rows. NEMO leaves unbound variables in negative patterns, including repeated variables that constrain which tuple would refute the condition.

## Next step

Open the Gunray PR, verify its CI, and leave it open.
