"""Yoke adjuster — moves the controls to where agents reach.

The core principle (Casey's directive):
- Don't demand more from the agent's model or alignment
- Demand more from the vessel's automation

When we observe agents reaching for X when they need Y, we:
1. Add an alias: X → Y
2. Or rename Y to X
3. Or move Y to where X is

This module generates yoke-move proposals from observed behavior.
"""
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


YOKE_DIR = Path("/workspace/research/mavis-erised/yokes")
YOKE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class YokeMove:
    """A proposed yoke move."""
    move_type: str  # "alias", "rename", "merge", "hide", "auto_translate"
    from_command: str
    to_command: Optional[str] = None
    rationale: str = ""
    evidence_count: int = 0
    confidence: float = 0.0
    proposed_at: str = ""


def propose_alias(target: str, agent_command: str, evidence_count: int) -> YokeMove:
    """Propose adding an alias: agent_command → target."""
    confidence = min(1.0, evidence_count / 5.0)
    return YokeMove(
        move_type="alias",
        from_command=agent_command,
        to_command=target,
        rationale=f"Agents reach for '{agent_command}' {evidence_count} times when '{target}' is the right command. Add '{agent_command}' as an alias for '{target}'.",
        evidence_count=evidence_count,
        confidence=confidence,
    )


def propose_rename(target: str, agent_command: str, evidence_count: int) -> YokeMove:
    """Propose renaming target to agent_command."""
    return YokeMove(
        move_type="rename",
        from_command=target,
        to_command=agent_command,
        rationale=f"Rename '{target}' to '{agent_command}' — that's what agents reach for naturally.",
        evidence_count=evidence_count,
        confidence=min(1.0, evidence_count / 10.0),
    )


def propose_auto_translate(command: str, evidence_count: int) -> YokeMove:
    """When agent uses command that doesn't exist, translate to the closest match."""
    return YokeMove(
        move_type="auto_translate",
        from_command=command,
        rationale=f"'{command}' isn't a real command. Auto-translate to the closest match.",
        evidence_count=evidence_count,
        confidence=0.5,
    )


def analyze_stumbles(stumbles: List[Dict]) -> List[YokeMove]:
    """Convert stumble observations into yoke moves."""
    moves = []
    seen = set()
    for s in stumbles:
        # If agents reach for X but should reach for Y, propose alias
        right = s.get("right_answer") or (
            list(s["success_after"].keys())[0] if s.get("success_after") else None
        )
        if right and right != s["first_command"]:
            key = (s["first_command"], right)
            if key not in seen:
                seen.add(key)
                moves.append(propose_alias(
                    target=right,
                    agent_command=s["first_command"],
                    evidence_count=s["agent_count"],
                ))
    return moves


def generate_aliases_from_vocabulary(
    intent_to_command: Dict[str, str],
    agent_reaches: Counter,
) -> List[YokeMove]:
    """Given what agents reach for and what's the right answer, generate aliases."""
    moves = []
    for reached, count in agent_reaches.items():
        # Find the closest intent
        if reached in intent_to_command:
            continue  # already correct
        # Look for fuzzy match
        for intent, cmd in intent_to_command.items():
            if intent.lower() in reached.lower() or reached.lower() in intent.lower():
                moves.append(propose_alias(cmd, reached, count))
                break
    return moves


def save_yoke_moves(moves: List[YokeMove]) -> Path:
    """Save yoke moves as a JSON file."""
    import datetime
    out_path = YOKE_DIR / f"yokes-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
    data = []
    for m in moves:
        data.append({
            "move_type": m.move_type,
            "from_command": m.from_command,
            "to_command": m.to_command,
            "rationale": m.rationale,
            "evidence_count": m.evidence_count,
            "confidence": m.confidence,
            "proposed_at": m.proposed_at,
        })
    out_path.write_text(json.dumps(data, indent=1))
    return out_path


def apply_alias(tool_module, alias: YokeMove) -> bool:
    """Apply an alias to a tool's CLI. (Stub — real impl modifies the CLI parser.)"""
    # In production, this would dynamically add the alias to argparse
    return True
