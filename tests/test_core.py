from pathlib import Path

import pytest

from jha_builder.__main__ import main
from jha_builder.core import Hazard, load_job, parse_job, render


def job(**hazard):
    base = {"hazard": "H", "severity": 3, "likelihood": 3, "controls": ["c"]}
    base.update(hazard)
    return {"job": "J", "steps": [{"step": "S1", "hazards": [base]}]}


def test_score_and_level_boundaries():
    assert Hazard("s", "h", 3, 5, ("c",)).level == "HIGH"
    assert Hazard("s", "h", 2, 4, ("c",)).level == "MEDIUM"
    assert Hazard("s", "h", 2, 3, ("c",)).level == "LOW"


def test_score_is_product():
    assert Hazard("s", "h", 4, 3, ("c",)).score == 12


def test_parse_ok():
    title, hazards = parse_job(job())
    assert title == "J" and hazards[0].step == "S1"


def test_missing_title():
    with pytest.raises(ValueError, match="title"):
        parse_job({"steps": []})


def test_no_hazards():
    with pytest.raises(ValueError, match="no hazards"):
        parse_job({"job": "J", "steps": []})


def test_severity_out_of_range():
    with pytest.raises(ValueError, match="severity"):
        parse_job(job(severity=6))


def test_likelihood_not_integer():
    with pytest.raises(ValueError, match="likelihood"):
        parse_job(job(likelihood="high"))


def test_hazard_without_controls_rejected():
    with pytest.raises(ValueError, match="no controls"):
        parse_job(job(controls=[]))


def test_load_example():
    title, hazards = load_job(Path("examples/rooftop-unit-replacement.json"))
    assert len(hazards) == 4 and "rooftop" in title


def test_render_summary_counts_high():
    title, hazards = parse_job(job(severity=5, likelihood=5))
    text = render(title, hazards)
    assert "High risk hazards: 1 of 1" in text and "HIGH" in text


def test_render_table_header():
    title, hazards = parse_job(job())
    assert render(title, hazards).splitlines()[2].startswith("| Step")


def test_cli_codes(tmp_path):
    assert main(["examples/rooftop-unit-replacement.json"]) == 0
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert main([str(bad)]) == 2
    assert main([str(tmp_path / "none.json")]) == 2
