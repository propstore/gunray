from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from gunray import (
    Answer,
    DefeasibleEvaluator,
    DefeasibleTheory,
    GroundAtom,
    GunrayEvaluator,
    MarkingPolicy,
    Rule,
)

ANTONIOU_PAGE_010 = "papers/Antoniou_2007_DefeasibleReasoningSemanticWeb/pngs/page-010.png"
Sections = dict[str, dict[str, set[tuple[str, ...]]]]


def _has(model_sections: Sections, section: str, atom: str) -> bool:
    return () in model_sections.get(section, {}).get(atom, set())


def _policy_model(theory: DefeasibleTheory, policy: MarkingPolicy) -> Sections:
    return DefeasibleEvaluator().evaluate(theory, marking_policy=policy).sections


def test_marking_policy_surface_is_explicitly_antoniou_propagating() -> None:
    """Antoniou 2007 p.10 distinguishes blocking from propagation."""

    assert ANTONIOU_PAGE_010.endswith("page-010.png")
    assert MarkingPolicy.BLOCKING.value == "blocking"
    assert MarkingPolicy.ANTONIOU_BLOCKING.value == "antoniou_blocking"
    assert MarkingPolicy.ANTONIOU_PROPAGATING.value == "antoniou_propagating"


def test_page_010_quaker_republican_has_gun_example_propagates_ambiguity() -> None:
    """Page-image source: ``ANTONIOU_PAGE_010``.

    The page's example makes ``pacifist(a)`` ambiguous. Blocking allows
    ``hasGun(a)`` because the dependent attacker cannot fire; propagation
    keeps the dependent conflict alive and blocks ``hasGun(a)``.
    """

    theory = DefeasibleTheory(
        facts={
            "quaker": {("a",)},
            "republican": {("a",)},
            "livesInChicago": {("a",)},
        },
        defeasible_rules=[
            Rule(id="r1", head="pacifist(X)", body=["quaker(X)"]),
            Rule(id="r2", head="~pacifist(X)", body=["republican(X)"]),
            Rule(id="r3", head="~hasGun(X)", body=["pacifist(X)"]),
            Rule(id="r4", head="hasGun(X)", body=["livesInChicago(X)"]),
        ],
        superiority=(("r3", "r4"),),
    )

    blocking = _policy_model(theory, MarkingPolicy.ANTONIOU_BLOCKING)
    propagating = _policy_model(theory, MarkingPolicy.ANTONIOU_PROPAGATING)

    assert ("a",) in blocking["yes"]["hasGun"]
    assert ("a",) not in propagating.get("yes", {}).get("hasGun", set())
    assert ("a",) in propagating["undecided"]["hasGun"]
    assert ("a",) in propagating["undecided"]["~hasGun"]


def test_reduced_page_010_fixture_shape_matches_policy_split() -> None:
    """Page-image source: ``ANTONIOU_PAGE_010`` reduced to zero arity."""

    theory = DefeasibleTheory(
        defeasible_rules=[
            Rule(id="r1", head="p", body=[]),
            Rule(id="r2", head="a", body=[]),
            Rule(id="r3", head="~a", body=[]),
            Rule(id="r4", head="~p", body=["a"]),
        ],
    )

    garcia = _policy_model(theory, MarkingPolicy.BLOCKING)
    blocking = _policy_model(theory, MarkingPolicy.ANTONIOU_BLOCKING)
    propagating = _policy_model(theory, MarkingPolicy.ANTONIOU_PROPAGATING)

    assert _has(garcia, "undecided", "p")
    assert _has(blocking, "yes", "p")
    assert _has(propagating, "undecided", "p")
    assert _has(propagating, "undecided", "~p")


def test_reduced_page_010_downstream_conclusion_becomes_undecided() -> None:
    """Page-image source: ``ANTONIOU_PAGE_010`` downstream propagation."""

    theory = DefeasibleTheory(
        defeasible_rules=[
            Rule(id="r1", head="p", body=[]),
            Rule(id="r2", head="a", body=[]),
            Rule(id="r3", head="~a", body=[]),
            Rule(id="r4", head="~p", body=["a"]),
            Rule(id="r5", head="q", body=["p"]),
        ],
    )

    blocking = _policy_model(theory, MarkingPolicy.ANTONIOU_BLOCKING)
    propagating = _policy_model(theory, MarkingPolicy.ANTONIOU_PROPAGATING)

    assert _has(blocking, "yes", "p")
    assert _has(blocking, "yes", "q")
    assert _has(propagating, "undecided", "p")
    assert _has(propagating, "undecided", "q")

    assert GunrayEvaluator().compare_marking_policies(
        theory,
        GroundAtom("q", ()),
        policies=(MarkingPolicy.ANTONIOU_BLOCKING, MarkingPolicy.ANTONIOU_PROPAGATING),
    ) == {
        Answer.YES: frozenset({MarkingPolicy.ANTONIOU_BLOCKING}),
        Answer.UNDECIDED: frozenset({MarkingPolicy.ANTONIOU_PROPAGATING}),
    }


def test_policy_comparison_uses_the_same_fact_rows_for_every_policy() -> None:
    theory = DefeasibleTheory(facts={"observed": iter([("a",), ("b",)])})
    policies = (*MarkingPolicy, MarkingPolicy.BLOCKING)

    assert GunrayEvaluator().compare_marking_policies(
        theory, GroundAtom("observed", ("b",)), policies=iter(policies)
    ) == {Answer.YES: frozenset(MarkingPolicy)}


def test_policy_comparison_reports_omitted_literals_as_unknown() -> None:
    theory = DefeasibleTheory(facts={"observed": [("a",)]})

    assert GunrayEvaluator().compare_marking_policies(
        theory, GroundAtom("observed", ("b",)), policies=MarkingPolicy
    ) == {Answer.UNKNOWN: frozenset(MarkingPolicy)}


def test_policy_comparison_requires_a_policy() -> None:
    with pytest.raises(ValueError, match="At least one marking policy"):
        GunrayEvaluator().compare_marking_policies(
            DefeasibleTheory(), GroundAtom("q", ()), policies=()
        )


@given(
    root=st.sampled_from(["p", "r", "s"]),
    ambiguous=st.sampled_from(["a", "b", "c"]),
    downstream=st.sampled_from(["q", "t", "u"]),
)
@settings(max_examples=20)
def test_propagation_blocks_supported_ambiguous_attack_chains(
    root: str,
    ambiguous: str,
    downstream: str,
) -> None:
    theory = DefeasibleTheory(
        defeasible_rules=[
            Rule(id="root", head=root, body=[]),
            Rule(id="ambiguous", head=ambiguous, body=[]),
            Rule(id="counter_ambiguous", head=f"~{ambiguous}", body=[]),
            Rule(id="counter_root", head=f"~{root}", body=[ambiguous]),
            Rule(id="downstream", head=downstream, body=[root]),
        ],
    )

    sections = _policy_model(theory, MarkingPolicy.ANTONIOU_PROPAGATING)

    assert _has(sections, "undecided", root)
    assert _has(sections, "undecided", f"~{root}")
    assert _has(sections, "undecided", downstream)


@given(atom=st.sampled_from(["p", "q", "r"]))
@settings(max_examples=10)
def test_propagation_is_conservative_without_reachable_ambiguity(atom: str) -> None:
    theory = DefeasibleTheory(
        defeasible_rules=[
            Rule(id="support", head=atom, body=[]),
            Rule(id="unreachable_counter", head=f"~{atom}", body=["missing"]),
        ],
    )

    assert _policy_model(theory, MarkingPolicy.ANTONIOU_PROPAGATING) == _policy_model(
        theory,
        MarkingPolicy.ANTONIOU_BLOCKING,
    )


@given(atom=st.sampled_from(["p", "q", "r"]))
@settings(max_examples=10)
def test_priority_resolving_conflict_makes_policies_agree(atom: str) -> None:
    theory = DefeasibleTheory(
        defeasible_rules=[
            Rule(id="support", head=atom, body=[]),
            Rule(id="counter", head=f"~{atom}", body=[]),
        ],
        superiority=(("support", "counter"),),
    )

    assert _policy_model(theory, MarkingPolicy.ANTONIOU_PROPAGATING) == _policy_model(
        theory,
        MarkingPolicy.ANTONIOU_BLOCKING,
    )
