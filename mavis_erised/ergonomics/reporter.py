"""Ergonomics reporter — generates the "did the plane fly right?" report.

The report answers:
1. How intuitive are our tools to zero-shot agents?
2. Where do agents stumble?
3. What yoke-moves should we make?
4. How do we design CTM/TFM models on top of this?
"""
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from ..behavior.recorder import (
    BehaviorProfile, Reach,
    first_reach_distribution, zero_shot_success_rate,
    stumble_patterns, compute_reach_frequency,
)
from ..yoke.adjuster import (
    YokeMove, propose_alias, analyze_stumbles, save_yoke_moves,
)


ERISED_REPORTS = Path("/workspace/research/mavis-erised/reports")
ERISED_REPORTS.mkdir(parents=True, exist_ok=True)


def generate_ergonomics_report(profiles: List[BehaviorProfile]) -> Dict:
    """Generate the full ergonomics report."""
    total_agents = len(profiles)
    zsr = zero_shot_success_rate(profiles)
    first_reach = first_reach_distribution(profiles)
    reach_freq = compute_reach_frequency(profiles)
    stumbles = stumble_patterns(profiles)
    yoke_moves = analyze_stumbles(stumbles)

    # Categorize: how much "training" do agents need?
    training_needed_pct = 100 * (1.0 - zsr)

    return {
        "summary": {
            "total_agents": total_agents,
            "zero_shot_success_rate": zsr,
            "training_needed_pct": training_needed_pct,
            "ergonomic_grade": grade_ergonomics(zsr),
        },
        "first_reach_distribution": first_reach,
        "reach_frequency": reach_freq,
        "stumbles": stumbles,
        "yoke_moves": [
            {
                "move_type": m.move_type,
                "from_command": m.from_command,
                "to_command": m.to_command,
                "rationale": m.rationale,
                "confidence": m.confidence,
            }
            for m in yoke_moves
        ],
        "design_implications": {
            "ctm": "CTM models should have these commands as natural primitives",
            "tfm": "TFM time-first models should optimize first-reach-to-success time",
            "origin_centric": "Origin-centric models should expose intent directly",
            "sfm": "SFM simulation-first should let agents reach for the simulated outcome",
        },
    }


def grade_ergonomics(zero_shot_rate: float) -> str:
    """A: 0.9+, B: 0.7-0.9, C: 0.5-0.7, D: <0.5."""
    if zero_shot_rate >= 0.9:
        return "A"
    elif zero_shot_rate >= 0.7:
        return "B"
    elif zero_shot_rate >= 0.5:
        return "C"
    else:
        return "D"


def save_report(report: Dict) -> Path:
    """Save the report to disk."""
    import datetime
    out_path = ERISED_REPORTS / f"report-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%SZ')}.json"
    out_path.write_text(json.dumps(report, indent=1))
    return out_path


def format_report_text(report: Dict) -> str:
    """Format the report as human-readable text."""
    lines = ["=" * 60, "ERISED ERGONOMICS REPORT", "=" * 60, ""]
    s = report["summary"]
    lines.append(f"Total agents tested: {s['total_agents']}")
    lines.append(f"Zero-shot success rate: {s['zero_shot_success_rate']:.1%}")
    lines.append(f"Training needed: {s['training_needed_pct']:.1f}%")
    lines.append(f"Ergonomic grade: {s['ergonomic_grade']}")
    lines.append("")

    lines.append("FIRST REACH DISTRIBUTION (what agents reach for first):")
    for cmd, count in sorted(report["first_reach_distribution"].items(),
                              key=lambda x: -x[1]):
        lines.append(f"  {count}x  {cmd}")
    lines.append("")

    lines.append("REACH FREQUENCY (all attempts):")
    for cmd, count in sorted(report["reach_frequency"].items(),
                              key=lambda x: -x[1]):
        lines.append(f"  {count}x  {cmd}")
    lines.append("")

    if report["stumbles"]:
        lines.append(f"STUMBLES ({len(report['stumbles'])} patterns):")
        for s in report["stumbles"][:5]:
            lines.append(f"  - Task: {s['task']}")
            count = s.get('first_try_failure_count', s.get('failure_count', 0))
            lines.append(f"    Agents reached: '{s['first_command']}' ({s['agent_count']} agents, {count} failed)")
            ra = s.get("right_answer") or (
                list(s.get("agents_eventually_used", {}).keys())[0]
                if s.get("agents_eventually_used") else "?"
            )
            lines.append(f"    Right answer: {ra}")
            lines.append(f"    Yoke move: {s['yoke_move']}")
        lines.append("")
        lines.append("")

    lines.append(f"YOKE MOVES ({len(report['yoke_moves'])} proposed):")
    for m in report["yoke_moves"][:5]:
        lines.append(f"  [{m['move_type']}] {m['from_command']} → {m['to_command'] or '(translate)'}")
        lines.append(f"      {m['rationale']}")
        lines.append(f"      confidence: {m['confidence']:.2f}")
    lines.append("")

    lines.append("DESIGN IMPLICATIONS:")
    for model, implication in report["design_implications"].items():
        lines.append(f"  {model.upper()}: {implication}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)
