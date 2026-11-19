"""Build a Job Hazard Analysis (JHA) sheet with a risk ranking from a JSON job file."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

LEVELS = ((15, "HIGH"), (8, "MEDIUM"), (1, "LOW"))


@dataclass(frozen=True)
class Hazard:
    """One hazard on one job step."""

    step: str
    description: str
    severity: int
    likelihood: int
    controls: tuple[str, ...]

    @property
    def score(self) -> int:
        """Risk score: severity times likelihood (each 1 to 5)."""
        return self.severity * self.likelihood

    @property
    def level(self) -> str:
        """HIGH from 15, MEDIUM from 8, otherwise LOW."""
        return next(name for floor, name in LEVELS if self.score >= floor)


def parse_job(data: dict) -> tuple[str, list[Hazard]]:
    """Validate job data and return the title and hazards in step order."""
    title = data.get("job")
    if not title:
        raise ValueError("job title is missing")
    hazards: list[Hazard] = []
    for step in data.get("steps", []):
        for h in step.get("hazards", []):
            sev, lik = h.get("severity"), h.get("likelihood")
            for name, val in (("severity", sev), ("likelihood", lik)):
                if not isinstance(val, int) or not 1 <= val <= 5:
                    raise ValueError(f"step '{step.get('step')}': {name} must be a whole number 1 to 5")
            controls = tuple(h.get("controls", []))
            if not controls:
                raise ValueError(f"step '{step.get('step')}': hazard '{h.get('hazard')}' has no controls")
            hazards.append(Hazard(step["step"], h["hazard"], sev, lik, controls))
    if not hazards:
        raise ValueError("job has no hazards")
    return title, hazards


def load_job(path: Path) -> tuple[str, list[Hazard]]:
    """Read and validate a job JSON file."""
    return parse_job(json.loads(path.read_text(encoding="utf-8")))


def render(title: str, hazards: list[Hazard]) -> str:
    """Return the JHA as Markdown, with a summary of high risk items."""
    lines = [f"# Job Hazard Analysis: {title}", "",
             "| Step | Hazard | S | L | Score | Level | Controls |",
             "|---|---|---|---|---|---|---|"]
    for h in hazards:
        lines.append(f"| {h.step} | {h.description} | {h.severity} | {h.likelihood} | "
                     f"{h.score} | {h.level} | {'; '.join(h.controls)} |")
    high = [h for h in hazards if h.level == "HIGH"]
    lines += ["", f"High risk hazards: {len(high)} of {len(hazards)}"]
    lines += [f"- {h.step}: {h.description}" for h in high]
    lines += ["", "Reviewed by: ____________  Date: ____________"]
    return "\n".join(lines)
