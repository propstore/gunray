"""Ground-atom disagreement, Garcia & Simari 2004 Definition 3.3.

Garcia & Simari 2004 Def 3.3 (verbatim):

    Two literals h1 and h2 disagree if and only if the set
    Pi union {h1, h2} is contradictory.

Here "contradictory" means the strict closure of that set contains a
pair of complementary literals. The trivial case is strong negation
(``p`` vs ``~p``); the interesting case is when strict rules connect
non-complementary literals and closing ``Pi union {h1, h2}`` under
those strict rules yields a contradiction.

Strict closure propagates rule heads until no more atoms are derivable.
Each evaluation shares the closure of Pi and memoizes whether each
pair of ground literals disagrees in that context.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field

from .types import GroundAtom, GroundDefeasibleRule, Scalar


@dataclass(frozen=True, slots=True)
class StrictContext:
    """Ground strict knowledge and disagreement results for one evaluation."""

    strict_rules: tuple[GroundDefeasibleRule, ...]
    facts: InitVar[frozenset[GroundAtom]]
    conflicts: frozenset[tuple[str, str]]
    pi_closure: frozenset[GroundAtom] = field(init=False)
    _disagreements: dict[frozenset[GroundAtom], bool] = field(
        init=False, default_factory=dict[frozenset[GroundAtom], bool], compare=False, repr=False
    )

    def __post_init__(self, facts: frozenset[GroundAtom]) -> None:
        object.__setattr__(self, "pi_closure", strict_closure(facts, self.strict_rules))

    def disagrees(self, left: GroundAtom, right: GroundAtom) -> bool:
        pair = frozenset({left, right})
        result = self._disagreements.get(pair)
        if result is None:
            result = disagrees(left, right, self.strict_rules, self.pi_closure, self.conflicts)
            self._disagreements[pair] = result
        return result


def complement(atom: GroundAtom) -> GroundAtom:
    """Return the complementary ground atom under strong negation.

    The strong-negation convention (``parser.py`` ``_complement``) is
    that ``~p`` is encoded as a ``~`` prefix on the predicate name
    with the same arguments. ``complement`` toggles that prefix.
    """

    predicate = atom.predicate
    if predicate.startswith("~"):
        return GroundAtom(predicate=predicate[1:], arguments=atom.arguments)
    return GroundAtom(predicate=f"~{predicate}", arguments=atom.arguments)


def strict_closure(
    seeds: frozenset[GroundAtom],
    strict_rules: tuple[GroundDefeasibleRule, ...],
    facts: frozenset[GroundAtom] = frozenset(),
) -> frozenset[GroundAtom]:
    """Forward-chain ``seeds`` plus strict ``facts`` under the ground strict rules.

    Only rules with ``kind == "strict"`` are propagated. Callers may pass
    a heterogeneous tuple.
    """

    closure: set[GroundAtom] = set(seeds) | set(facts)
    changed = True
    while changed:
        changed = False
        for rule in strict_rules:
            if rule.kind != "strict":
                continue
            if rule.head in closure:
                continue
            if all(atom in closure for atom in rule.body):
                closure.add(rule.head)
                changed = True
    return frozenset(closure)


def disagrees(
    h1: GroundAtom,
    h2: GroundAtom,
    strict_context: tuple[GroundDefeasibleRule, ...],
    facts: frozenset[GroundAtom] = frozenset(),
    conflicts: frozenset[tuple[str, str]] = frozenset(),
) -> bool:
    """Return True iff ``{h1, h2}`` is contradictory under ``strict_context``.

    Garcia & Simari 2004 Def 3.3: two literals disagree iff their
    union with ``Pi`` is contradictory. ``Pi`` includes strict facts
    as well as strict rules, so callers pass grounded facts separately
    from ``strict_context``. We compute the strict closure of
    ``{h1, h2}`` under that strict knowledge base and return True iff
    any atom in that closure has its complement also present.
    """

    if h1 == complement(h2):
        return True
    if _explicitly_conflict(h1, h2, conflicts):
        return True
    closure = strict_closure(frozenset({h1, h2}), strict_context, facts=facts)
    return has_contradiction(closure, conflicts=conflicts)


def has_contradiction(
    closure: frozenset[GroundAtom],
    *,
    conflicts: frozenset[tuple[str, str]] = frozenset(),
) -> bool:
    for atom in closure:
        if complement(atom) in closure:
            return True
    if not conflicts:
        return False

    arguments_by_predicate: dict[str, set[tuple[Scalar, ...]]] = {}
    for atom in closure:
        arguments_by_predicate.setdefault(atom.predicate, set()).add(atom.arguments)
    for left, right in conflicts:
        left_arguments = arguments_by_predicate.get(left)
        right_arguments = arguments_by_predicate.get(right)
        if left_arguments is not None and right_arguments is not None:
            if not left_arguments.isdisjoint(right_arguments):
                return True
    return False


def _explicitly_conflict(
    left: GroundAtom,
    right: GroundAtom,
    conflicts: frozenset[tuple[str, str]],
) -> bool:
    return left.arguments == right.arguments and (left.predicate, right.predicate) in conflicts
