import pytest

from gunray import (
    Constant,
    DatalogDerivation,
    GroundAtom,
    GunrayEvaluator,
    NegationSemantics,
    Program,
    TraceConfig,
    evaluate_program_file,
    evaluate_program_file_with_trace,
    parse_atom_text,
)
from gunray.errors import ParseError, SafetyViolationError
from gunray.types import Comparison

CAPTURE = TraceConfig(capture_derivations=True)


def test_file_derivations_follow_recursive_premises_outside_query(tmp_path):
    path = tmp_path / "routes.gnr"
    path.write_text(
        "facts: {link: [[a, b], [b, c]]}\n"
        "rules:\n"
        "  - 'reachable(X,Y) :- link(X,Y).'\n"
        "  - 'reachable(X,Z) :- link(X,Y), reachable(Y,Z).'\n"
        "  - 'destination(Y) :- reachable(\"a\",Y).'\n",
        encoding="utf-8",
    )
    facts = {"link": [("c", "d")]}
    model, trace = evaluate_program_file_with_trace(
        path, facts=facts, query="destination", trace_config=CAPTURE
    )

    assert model == evaluate_program_file(path, facts=facts, query="destination")
    assert model.facts == {"destination": {("b",), ("c",), ("d",)}}
    assert trace.derivation_for(GroundAtom("destination", ("d",))) == DatalogDerivation(
        'destination(Y) :- reachable("a",Y).', (GroundAtom("reachable", ("a", "d")),)
    )
    assert trace.derivation_for(GroundAtom("reachable", ("a", "d"))) == DatalogDerivation(
        "reachable(X,Z) :- link(X,Y), reachable(Y,Z).",
        (GroundAtom("link", ("a", "b")), GroundAtom("reachable", ("b", "d"))),
    )
    assert trace.derivation_for(GroundAtom("reachable", ("b", "d"))) == DatalogDerivation(
        "reachable(X,Z) :- link(X,Y), reachable(Y,Z).",
        (GroundAtom("link", ("b", "c")), GroundAtom("reachable", ("c", "d"))),
    )
    added_fact = GroundAtom("link", ("c", "d"))
    assert trace.derivation_for(GroundAtom("reachable", ("c", "d"))) == DatalogDerivation(
        "reachable(X,Y) :- link(X,Y).", (added_fact,)
    )
    assert trace.derivation_for(added_fact) == DatalogDerivation(None)
    assert trace.derivation_for(GroundAtom("destination", ("a",))) is None


def test_trace_records_one_witness_in_rule_order_with_conditions():
    rule = "chosen(X) :- option(X,_,W), goal(X), W + 1 >= 3, not blocked(X,_)."
    program = Program(
        facts={
            "option": [("a", "matched", 2), ("b", "other", 1)],
            "goal": [("a",)],
            "backup": [("a",)],
            "blocked": [("b", "elsewhere")],
            "chosen": [("given",)],
        },
        rules=[rule, "chosen(X) :- backup(X).", 'chosen("given").', 'chosen("literal").'],
    )
    evaluator = GunrayEvaluator()
    model, trace = evaluator.evaluate_with_trace(program, trace_config=CAPTURE)

    assert model == evaluator.evaluate(program)
    assert trace.derivation_for(GroundAtom("chosen", ("a",))) == DatalogDerivation(
        rule,
        (GroundAtom("option", ("a", "matched", 2)), GroundAtom("goal", ("a",))),
        (parse_atom_text('blocked("a",_)'),),
        (Comparison(Constant(3), ">=", Constant(3)),),
    )
    assert trace.derivation_for(GroundAtom("chosen", ("given",))) == DatalogDerivation(None)
    assert trace.derivation_for(GroundAtom("chosen", ("literal",))) == DatalogDerivation(
        'chosen("literal").'
    )


def test_existential_negation_retains_repeated_variables_and_bound_terms():
    rule = "open(X) :- candidate(X,N), not pair(X,N + 1,Y,Y)."
    program = Program(
        facts={
            "candidate": [("a", 4), ("b", 4)],
            "pair": [("a", 5, "left", "right"), ("b", 5, "same", "same")],
        },
        rules=[rule],
    )
    evaluator = GunrayEvaluator()
    with pytest.raises(SafetyViolationError):
        evaluator.evaluate_with_trace(program, trace_config=CAPTURE)

    model, trace = evaluator.evaluate_with_trace(
        program, trace_config=CAPTURE, negation_semantics=NegationSemantics.NEMO
    )
    assert model == evaluator.evaluate(program, negation_semantics=NegationSemantics.NEMO)
    assert model.facts["open"] == {("a",)}
    assert trace.derivation_for(GroundAtom("open", ("a",))) == DatalogDerivation(
        rule,
        (GroundAtom("candidate", ("a", 4)),),
        (parse_atom_text('pair("a",5,Y,Y)'),),
    )
    assert trace.derivation_for(GroundAtom("open", ("b",))) is None


def test_trace_without_derivations_has_no_derivation_storage():
    program = Program(facts={"source": [("a",)]}, rules=["answer(X) :- source(X)."])
    model, trace = GunrayEvaluator().evaluate_with_trace(
        program, trace_config=TraceConfig(capture_derived_rows=True)
    )
    assert model.facts["answer"] == {("a",)}
    assert trace.find_rule_fires(head_predicate="answer")[0].derived_rows == (("a",),)
    assert trace.derivations is None
    with pytest.raises(ValueError, match="were not captured"):
        trace.derivation_for(GroundAtom("answer", ("a",)))


def test_file_trace_preserves_rule_line_in_diagnostics(tmp_path):
    path = tmp_path / "invalid.gnr"
    path.write_text("rules:\n  - 'broken(.'\n", encoding="utf-8")
    with pytest.raises(ParseError) as error:
        evaluate_program_file_with_trace(path, trace_config=CAPTURE)
    assert f"{path}:2:" in str(error.value)
