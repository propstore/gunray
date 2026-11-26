# Plain Datalog program files

**Goal** Run declarative Datalog models from files and locate invalid rules for the caller.

**State** The CLI accepts YAML or JSON programs, optional additional facts and an optional relation query. The Python entry point returns a Gunray model.

**Decisions and why** Use the existing Program fields and rule grammar. Bare YAML fact strings and quoted rule constants work with existing models. Existing conformance programs use lowercase rule variables.

**Surprises** The motivating inheritance experiment used a bare object label in a negated literal. The evaluator correctly rejected the unbound variable but the user had no rule location.

**Verification** The file API regenerated the same 12 inheritance histories as the in-memory model. Managed server sessions on the two engines each reported 13 passed including admission. The focused program-file tests reported four passes. Ruff and Pyright passed.

**Next step** Run the full repository CI on the published branch.
