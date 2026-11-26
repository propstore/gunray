import json

import pytest

from gunray import evaluate_program_file
from gunray.cli import main
from gunray.errors import ParseError, SafetyViolationError


def test_file_query_and_extra_facts(tmp_path, capsys):
    path = tmp_path / "example.gnr"
    path.write_text("facts: {edge: [[leaf, b]]}\nrules: ['out(x) :- edge(\"leaf\",x).']\n")
    additions = tmp_path / "extra.json"
    additions.write_text('{"edge":[["leaf","c"],["leaf","b"]]}')
    assert main(["run", str(path), "--facts", str(additions), "--query", "out"]) == 0
    assert json.loads(capsys.readouterr().out) == {"out": [["b"], ["c"]]}
    assert evaluate_program_file(path).facts["out"] == {("b",)}


def test_unsafe_bare_term_reports_its_rule(tmp_path, capsys):
    path = tmp_path / "unsafe.gnr"
    path.write_text("rules:\n  - 'ok(x) :- seed(x).'\n  - 'bad(x) :- ok(x), not tag(leaf).'\n")
    with pytest.raises(SafetyViolationError, match="Quote string constants"):
        evaluate_program_file(path)
    assert main(["run", str(path)]) == 2
    err = capsys.readouterr().err
    assert f"{path}:3:" in err
    assert "leaf" in err


def test_malformed_rule_reports_source_line(tmp_path):
    path = tmp_path / "broken.gnr"
    path.write_text("rules:\n  - 'broken(.'\n")
    with pytest.raises(ParseError) as error:
        evaluate_program_file(path)
    assert f"{path}:2:" in str(error.value)


def test_empty_query_and_unknown_name_are_distinct(tmp_path, capsys):
    path = tmp_path / "program.json"
    path.write_text('{"rules":["out(X) :- source(X)."]}')
    assert main(["run", str(path), "--query", "out"]) == 0
    assert json.loads(capsys.readouterr().out) == {"out": []}
    assert main(["run", str(path), "--query", "typo"]) == 2
    assert "Unknown relation 'typo'" in capsys.readouterr().err
