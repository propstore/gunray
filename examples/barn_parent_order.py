"""Select and emit bounded MOO tests for reordering an ancestor's parents."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import combinations, permutations, product
from pathlib import Path
from typing import cast

import yaml

from gunray import evaluate_program_file
from gunray.schema import FactTuple

SUITE = "gunray_parent_reorder"
PROGRAM = Path(__file__).with_suffix(".gnr")
Graph = tuple[tuple[int, ...], ...]
Step = dict[str, object]


@dataclass(frozen=True)
class Case:
    graph: Graph
    changed: int
    definitions: tuple[int, int]
    before: int
    after: int
    breadth_first: tuple[int, int]

    @property
    def direct(self) -> bool:
        return self.changed in self.graph[-1]

    @property
    def distinguishes_breadth_first(self) -> bool:
        return (self.before, self.after) != self.breadth_first


def graphs(size: int) -> Iterator[Graph]:
    # Topological labels give the generator finite domains of distinct,
    # already-created parents. Boyapati et al., Korat, Sec. 3.1, p. 126.
    choices = [
        ((), *permutations(range(node), 1), *permutations(range(node), 2)) for node in range(size)
    ]
    return product(*choices)


def path_facts(size: int) -> dict[str, list[FactTuple]]:
    paths = sorted(path for depth in range(size) for path in product((0, 1), repeat=depth))
    ids = {path: index for index, path in enumerate(paths)}
    return {
        "empty_path": [(ids[()],)],
        "extend": [(ids[path[:-1]], path[-1], ids[path]) for path in paths if path],
        # Pre-order sorts by parent-position path. Sorting first by length
        # models the historical breadth-first traversal for the control.
        "rank": [
            *(("depth", ids[path], index) for index, path in enumerate(paths)),
            *(
                ("breadth", ids[path], index)
                for index, path in enumerate(sorted(paths, key=lambda path: (len(path), path)))
            ),
        ],
        "competing": list(combinations(range(size - 1), 2)),
    }


def reordered(graph: Graph, changed: int) -> Graph:
    return graph[:changed] + (graph[changed][::-1],) + graph[changed + 1 :]


def candidates(graph: Graph, order: dict[str, list[FactTuple]]) -> Iterator[Case]:
    receiver = len(graph) - 1
    reachable = reachable_from(graph, receiver)
    swaps = [node for node in range(receiver) if node in reachable and len(graph[node]) == 2]
    if not swaps:
        return
    states = {-1: graph, **{node: reordered(graph, node) for node in swaps}}
    rows = evaluate_program_file(
        PROGRAM,
        facts={
            **order,
            "root": [(state, receiver) for state in states],
            "parent": [
                (state, child, position, parent)
                for state, parents in states.items()
                for child, ordered in enumerate(parents)
                for position, parent in enumerate(ordered)
            ],
        },
        query="winner",
    ).facts["winner"]
    winners = {
        (mode, state, a, b): winner
        for mode, state, a, b, winner in cast(set[tuple[str, int, int, int, int]], rows)
    }
    for changed in swaps:
        for a, b in combinations(range(receiver), 2):
            before = winners.get(("depth", -1, a, b))
            if before is None:
                continue
            yield Case(
                graph,
                changed,
                (a, b),
                before,
                winners["depth", changed, a, b],
                (winners["breadth", -1, a, b], winners["breadth", changed, a, b]),
            )


def reachable_from(graph: Graph, receiver: int) -> set[int]:
    # With topological labels, one descending scan reaches every ancestor.
    reached = {receiver}
    for node in range(receiver, -1, -1):
        if node in reached:
            reached.update(graph[node])
    return reached


def select_cases() -> tuple[dict[str, Case], int, int]:
    selected: dict[str, Case] = {}
    graph_count = 0
    candidate_count = 0
    for size in (4, 5):
        order = path_facts(size)
        for graph in graphs(size):
            graph_count += 1
            for candidate in candidates(graph, order):
                candidate_count += 1
                if candidate.before == candidate.after:
                    selected.setdefault("unchanged", candidate)
                    continue
                distance = "direct" if candidate.direct else "indirect"
                traversal = "depth" if candidate.distinguishes_breadth_first else "either"
                selected.setdefault(f"{distance}_{traversal}", candidate)
    return selected, graph_count, candidate_count


def install(obj: str, name: str, code: str) -> list[Step]:
    return [
        {
            "run": f'add_verb({obj}, {{player, "rxd", "{name}"}}, {{"this", "none", "this"}})',
            "expect": {"value": 1},
        },
        {
            "run": f"return set_verb_code({obj}, 1, {{{json.dumps(code)}}});",
            "expect": {"value": []},
        },
    ]


def create_arm(arm: str, graph: Graph, definitions: tuple[int, int]) -> list[Step]:
    steps: list[Step] = []
    for node, parents in enumerate(graph):
        arguments = ", ".join("{" + f"{arm}_{parent}" + "}" for parent in parents)
        parent_list = "{" + arguments + "}" if parents else "$nothing"
        steps.append(
            {"run": f"create({parent_list})", "capture": f"{arm}_{node}", "expect": {"type": "obj"}}
        )
        obj = "{" + f"{arm}_{node}" + "}"
        if node in definitions:
            steps.extend(install(obj, "order_marker", f'return "node_{node}";'))
        if node == len(graph) - 1:
            # Both warmed reads go through this same compiled verb call site.
            steps.extend(install(obj, "order_probe", "return this:order_marker();"))
    return steps


def render_case(label: str, case: Case) -> tuple[dict[str, object], dict[str, object]]:
    name = f"{SUITE}_{label}"
    receiver = len(case.graph) - 1
    final_graph = reordered(case.graph, case.changed)
    parent_left, parent_right = final_graph[case.changed]
    expected = [f"node_{case.before}", f"node_{case.after}", f"node_{case.after}"]
    steps: list[Step] = [
        {"restart_server": {"reset_db": True}},
        *create_arm("cold", final_graph, case.definitions),
        *create_arm("warm", case.graph, case.definitions),
        {"run": f"{{warm_{receiver}}}:order_probe()", "capture": "before"},
        {
            "run": (
                f"chparents({{warm_{case.changed}}}, "
                f"{{{{warm_{parent_left}}}, {{warm_{parent_right}}}}})"
            ),
            "expect": {"value": 0},
        },
        {
            "run": (
                f'case_id = "{name}"; '
                f"return {{{{before}}, {{warm_{receiver}}}:order_probe(), "
                f"{{cold_{receiver}}}:order_probe()}};"
            ),
            "expect": {"value": expected},
        },
    ]
    cleanup = [
        {"run": f"recycle({{{arm}_{node}}})"}
        for arm in ("warm", "cold")
        for node in reversed(range(len(case.graph)))
    ]
    return (
        {"name": name, "permission": "wizard", "steps": steps, "cleanup": cleanup},
        {
            "parents": case.graph,
            "reordered_object": case.changed,
            "definitions": case.definitions,
            "expected": expected,
            "breadth_first": [f"node_{node}" for node in case.breadth_first],
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Managed runner's output directory")
    args = parser.parse_args()
    cases_dir = args.run / "candidate" / "cases"
    evidence = args.run / "evidence"
    cases_dir.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)

    selected, graph_count, candidate_count = select_cases()
    trials = [render_case(label, case) for label, case in sorted(selected.items())]
    suite = {
        "name": SUITE,
        "description": "Descendant lookup after reordering an ancestor's parents",
        "requires": {"config": ["managed_server"]},
        "tests": [test for test, _ in trials],
    }
    predictions = {
        "graph_count": graph_count,
        "candidate_count": candidate_count,
        "observations": ["warm_before", "warm_after", "cold_after"],
        "cases": {test["name"]: prediction for test, prediction in trials},
    }
    (cases_dir / f"{SUITE}.yaml").write_text(
        yaml.safe_dump(suite, sort_keys=False), encoding="utf-8"
    )
    (evidence / "predictions.json").write_text(
        json.dumps(predictions, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
