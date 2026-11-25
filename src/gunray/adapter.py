"""Single-object dispatcher over Gunray-owned input types."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from typing import cast, overload

from ._internal import _answer_from_model
from .answer import Answer
from .closure import ClosureEvaluator
from .defeasible import DefeasibleEvaluator
from .evaluator import SemiNaiveEvaluator
from .schema import (
    ClosurePolicy,
    DefeasibleModel,
    DefeasibleTheory,
    GroundingMode,
    MarkingPolicy,
    Model,
    NegationSemantics,
    Program,
    ProjectionSemantics,
)
from .trace import DatalogTrace, DefeasibleTrace, TraceConfig
from .types import GroundAtom


class GunrayEvaluator:
    """Dispatch Gunray inputs to the right engine."""

    def __init__(self) -> None:
        self._datalog = SemiNaiveEvaluator()
        self._defeasible = DefeasibleEvaluator()
        self._closure = ClosureEvaluator()
        self._bridge: object | None = None

    def _suite_bridge(self) -> object:
        if self._bridge is None:
            from .conformance_adapter import GunrayConformanceEvaluator

            self._bridge = GunrayConformanceEvaluator(core=self)
        return self._bridge

    @overload
    def evaluate(
        self,
        item: Program,
        *,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
    ) -> Model: ...

    @overload
    def evaluate(
        self,
        item: DefeasibleTheory,
        *,
        marking_policy: MarkingPolicy = MarkingPolicy.BLOCKING,
        closure_policy: ClosurePolicy | None = None,
        grounding_mode: GroundingMode = GroundingMode.DIRECT,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
        projection_semantics: ProjectionSemantics = ProjectionSemantics.GARCIA,
        max_arguments: int | None = None,
    ) -> DefeasibleModel: ...

    def evaluate(
        self,
        item: Program | DefeasibleTheory,
        *,
        marking_policy: MarkingPolicy = MarkingPolicy.BLOCKING,
        closure_policy: ClosurePolicy | None = None,
        grounding_mode: GroundingMode = GroundingMode.DIRECT,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
        projection_semantics: ProjectionSemantics = ProjectionSemantics.GARCIA,
        max_arguments: int | None = None,
    ) -> Model | DefeasibleModel:
        if isinstance(item, Program):
            return self._datalog.evaluate(item, negation_semantics=negation_semantics)
        if isinstance(item, DefeasibleTheory):
            if closure_policy is not None:
                if grounding_mode is not GroundingMode.DIRECT:
                    raise ValueError("grounding_mode applies only to dialectical-tree evaluation")
                if projection_semantics is not ProjectionSemantics.GARCIA:
                    raise ValueError("projection_semantics applies only to defeasible projection")
                return self._closure.evaluate(item, closure_policy)
            return self._defeasible.evaluate(
                item,
                marking_policy=marking_policy,
                closure_policy=closure_policy,
                grounding_mode=grounding_mode,
                negation_semantics=negation_semantics,
                projection_semantics=projection_semantics,
                max_arguments=max_arguments,
            )
        return cast(Model | DefeasibleModel, self._suite_bridge().evaluate(item, None))  # type: ignore[attr-defined]

    @overload
    def evaluate_with_trace(
        self,
        item: Program,
        trace_config: TraceConfig | None = None,
        *,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
    ) -> tuple[Model, DatalogTrace]: ...

    @overload
    def evaluate_with_trace(
        self,
        item: DefeasibleTheory,
        trace_config: TraceConfig | None = None,
        *,
        marking_policy: MarkingPolicy = MarkingPolicy.BLOCKING,
        closure_policy: ClosurePolicy | None = None,
        grounding_mode: GroundingMode = GroundingMode.DIRECT,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
        projection_semantics: ProjectionSemantics = ProjectionSemantics.GARCIA,
        max_arguments: int | None = None,
    ) -> tuple[DefeasibleModel, DefeasibleTrace]: ...

    def evaluate_with_trace(
        self,
        item: Program | DefeasibleTheory,
        trace_config: TraceConfig | None = None,
        *,
        marking_policy: MarkingPolicy = MarkingPolicy.BLOCKING,
        closure_policy: ClosurePolicy | None = None,
        grounding_mode: GroundingMode = GroundingMode.DIRECT,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
        projection_semantics: ProjectionSemantics = ProjectionSemantics.GARCIA,
        max_arguments: int | None = None,
    ) -> tuple[Model | DefeasibleModel, DatalogTrace | DefeasibleTrace]:
        if isinstance(item, Program):
            return self._datalog.evaluate_with_trace(
                item,
                trace_config,
                negation_semantics=negation_semantics,
            )
        if isinstance(item, DefeasibleTheory):
            if closure_policy is not None:
                if grounding_mode is not GroundingMode.DIRECT:
                    raise ValueError("grounding_mode applies only to dialectical-tree evaluation")
                if projection_semantics is not ProjectionSemantics.GARCIA:
                    raise ValueError("projection_semantics applies only to defeasible projection")
                return self._closure.evaluate_with_trace(item, closure_policy, trace_config)
            return self._defeasible.evaluate_with_trace(
                item,
                trace_config,
                marking_policy=marking_policy,
                closure_policy=closure_policy,
                grounding_mode=grounding_mode,
                negation_semantics=negation_semantics,
                projection_semantics=projection_semantics,
                max_arguments=max_arguments,
            )
        return cast(
            tuple[Model | DefeasibleModel, DatalogTrace | DefeasibleTrace],
            self._suite_bridge().evaluate_with_trace(item, None, trace_config),  # type: ignore[attr-defined]
        )

    def compare_marking_policies(
        self,
        theory: DefeasibleTheory,
        literal: GroundAtom,
        *,
        policies: Iterable[MarkingPolicy],
    ) -> dict[Answer, frozenset[MarkingPolicy]]:
        """Group distinct selected policies by their answer to a ground literal.

        The policies for an answer form its support over this selection
        (Hellerstein 2026, Definition 3.2, p. 6). Omitted literals project to
        ``Answer.UNKNOWN``, as in the CLI. Evaluation errors propagate.
        """
        selected = dict.fromkeys(policies)
        if not selected:
            raise ValueError("At least one marking policy is required")

        # Fact rows can be one-shot iterables. Evaluate every policy on the same rows.
        snapshot = replace(theory, facts={name: tuple(rows) for name, rows in theory.facts.items()})
        support: dict[Answer, set[MarkingPolicy]] = {}
        for policy in selected:
            model = self.evaluate(snapshot, marking_policy=policy)
            answer = _answer_from_model(model, literal)
            support.setdefault(answer, set()).add(policy)
        return {answer: frozenset(group) for answer, group in support.items()}

    def satisfies_klm_property(
        self,
        theory: DefeasibleTheory,
        property_name: str,
        policy: ClosurePolicy,
    ) -> bool:
        if isinstance(theory, DefeasibleTheory):
            return self._closure.satisfies_klm_property(theory, property_name, policy)
        return self._suite_bridge().satisfies_klm_property(theory, property_name, policy)  # type: ignore[attr-defined]
