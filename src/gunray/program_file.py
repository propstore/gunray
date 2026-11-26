"""Read plain Datalog programs and their fact relations from YAML or JSON."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import yaml

from .errors import GunrayError
from .evaluator import SemiNaiveEvaluator
from .parser import parse_rule_text
from .schema import Model, PredicateFacts, Program, Scalar


class DocumentError(ValueError):
    """An input document has invalid fields or values."""


def _facts_from_data(raw: object) -> dict[str, list[tuple[Scalar, ...]]]:
    facts = _mapping(raw, "facts")
    result: dict[str, list[tuple[Scalar, ...]]] = {}
    for predicate, raw_rows in facts.items():
        if not isinstance(predicate, str):
            raise DocumentError("Fact predicates must be strings")
        rows = _sequence(raw_rows, f"facts.{predicate}")
        result[predicate] = [_row_from_data(row, f"facts.{predicate}") for row in rows]
    return result


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise DocumentError(f"{name} must be a mapping with string keys")
    mapping = cast(dict[object, object], value)
    if not all(isinstance(key, str) for key in mapping):
        raise DocumentError(f"{name} must be a mapping with string keys")
    return cast(dict[str, object], mapping)


def _sequence(value: object, name: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise DocumentError(f"{name} must be a list")
    return cast(Sequence[object], value)


def _row_from_data(value: object, name: str) -> tuple[Scalar, ...]:
    row = _sequence(value, name)
    values: list[Scalar] = []
    for item in row:
        if not isinstance(item, (str, int, float, bool)):
            raise DocumentError(f"{name} rows may contain only string, number, or boolean values")
        values.append(item)
    return tuple(values)


def _string(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise DocumentError(f"{name} must be a string")
    return value


def evaluate_program_file(
    path: str | Path, *, facts: PredicateFacts | None = None, query: str | None = None
) -> Model:
    """Evaluate the file's program with optional additional rows for any relation."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    try:
        raw = _mapping(yaml.safe_load(text), "program")
        extra = set(raw) - {"facts", "rules"}
        if extra:
            raise DocumentError(f"Unknown program fields: {', '.join(sorted(extra))}")
        rows = _facts_from_data(raw.get("facts", {}))
        for predicate, additions in (facts or {}).items():
            rows.setdefault(predicate, []).extend(additions)
        rules = [_string(s, "rule") for s in _sequence(raw.get("rules", []), "rules")]
        model = SemiNaiveEvaluator().evaluate(Program(facts=rows, rules=rules))
        if query is None:
            return model
        if query not in model.facts:
            # A declared relation with no derived rows may be absent from the model.
            parsed = (parse_rule_text(rule) for rule in rules)
            if not any(
                atom.predicate == query
                for rule in parsed
                for atom in (*rule.heads, *rule.positive_body, *rule.negative_body)
            ):
                raise DocumentError(f"Unknown relation {query!r}")
        return Model(facts={query: model.facts.get(query, set())})
    except GunrayError as exc:
        line = _rule_line(text, exc.rule_text) if exc.rule_text is not None else None
        location = f"{path}:{line}" if line is not None else str(path)
        raise type(exc)(f"{location}: {exc}") from exc
    except (DocumentError, yaml.YAMLError) as exc:
        raise DocumentError(f"{path}: {exc}") from exc


class _SyntaxTreeLoader(yaml.SafeLoader):
    def get_single_data(self) -> yaml.Node | None:
        return self.get_single_node()


def _rule_line(text: str, source: str) -> int | None:
    document: object = yaml.load(text, Loader=_SyntaxTreeLoader)
    if isinstance(document, yaml.MappingNode):
        for key, value in document.value:
            if key.value == "rules" and isinstance(value, yaml.SequenceNode):
                for node in value.value:
                    if isinstance(node, yaml.ScalarNode) and node.value.strip() == source.strip():
                        return node.start_mark.line + 1
    return None
