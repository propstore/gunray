import json
import subprocess
import sys
from pathlib import Path

import yaml


def test_generator_emits_managed_cases_and_predictions(tmp_path):
    script = Path(__file__).resolve().parents[1] / "examples" / "barn_parent_order.py"
    subprocess.run([sys.executable, str(script), str(tmp_path)], check=True)

    suite = yaml.safe_load((tmp_path / "candidate/cases/gunray_parent_reorder.yaml").read_text())
    predictions = json.loads((tmp_path / "evidence/predictions.json").read_text())
    cases = predictions["cases"]
    assert predictions["graph_count"] == 1800
    assert predictions["observations"] == ["warm_before", "warm_after", "cold_after"]
    assert suite["requires"] == {"config": ["managed_server"]}
    assert [test["name"] for test in suite["tests"]] == list(cases)
    for test in suite["tests"]:
        assert test["steps"][-1]["expect"]["value"] == cases[test["name"]]["expected"]

    for distance in ("direct", "indirect"):
        discriminator = cases[f"gunray_parent_reorder_{distance}_depth"]
        receiver_parents = discriminator["parents"][-1]
        assert (discriminator["reordered_object"] in receiver_parents) == (distance == "direct")
        assert discriminator["expected"] == ["node_0", "node_1", "node_1"]
        assert discriminator["breadth_first"] == ["node_0", "node_0"]
        either = cases[f"gunray_parent_reorder_{distance}_either"]
        assert either["expected"] == ["node_0", "node_1", "node_1"]
        assert either["breadth_first"] == ["node_0", "node_1"]

    unchanged = cases["gunray_parent_reorder_unchanged"]
    assert len(set(unchanged["expected"])) == 1
