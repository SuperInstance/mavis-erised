"""Behavior recorder — captures where agents instinctively reach.

Records every action an agent takes:
- What they tried first (intuitive reach)
- What they tried second (after first failed)
- Where they gave up
- Where they succeeded

This data drives the yoke-mover.
"""
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Reach:
    """A single agent reach attempt."""
    command: str
    success: bool
    attempt_number: int  # 1=first try, 2=second try, etc.
    intent_inferred: str = ""


@dataclass
class BehaviorProfile:
    """Behavior profile for a single agent on a single task."""
    agent_id: str
    task: str
    reach_sequence: List[Reach] = field(default_factory=list)
    final_success: bool = False
    attempts_to_success: int = 0


def record_reach(profile: BehaviorProfile, command: str, success: bool,
                 intent: str = "") -> None:
    """Record a single reach attempt."""
    attempt = len(profile.reach_sequence) + 1
    profile.reach_sequence.append(Reach(
        command=command,
        success=success,
        attempt_number=attempt,
        intent_inferred=intent,
    ))
    if success:
        profile.final_success = True
        if profile.attempts_to_success == 0:
            profile.attempts_to_success = attempt


def first_reach_distribution(profiles: List[BehaviorProfile]) -> Dict[str, int]:
    """What commands do agents reach for FIRST most often?"""
    counter = Counter()
    for p in profiles:
        if p.reach_sequence:
            counter[p.reach_sequence[0].command] += 1
    return dict(counter)


def zero_shot_success_rate(profiles: List[BehaviorProfile]) -> float:
    """What % of agents succeed on the FIRST try (zero-shot)?"""
    if not profiles:
        return 0.0
    first_try_success = sum(1 for p in profiles
                            if p.reach_sequence and p.reach_sequence[0].success)
    return first_try_success / len(profiles)


def stumble_patterns(profiles: List[BehaviorProfile]) -> List[Dict]:
    """Where do agents stumble? (reach for the wrong command repeatedly)"""
    from ..play import find_useful_commands

    # Group by (task, first_command)
    groups = defaultdict(list)
    for p in profiles:
        if p.reach_sequence:
            key = (p.task, p.reach_sequence[0].command)
            groups[key].append(p)

    stumbles = []
    for (task, first_cmd), group in groups.items():
        # If multiple agents tried the same first command and most FAILED ON FIRST TRY
        if len(group) >= 2:
            first_try_failures = sum(1 for p in group if not p.reach_sequence[0].success)
            if first_try_failures > len(group) / 2:
                # The "right answer" is the useful command for this task
                # (NOT just the first successful command — that's often 'help')
                useful = find_useful_commands(task, [])
                right_answer = useful[0] if useful else "unknown"

                # Track what they actually ended up using
                actual_success = Counter()
                for p in group:
                    for r in p.reach_sequence:
                        if r.success and r.command != first_cmd:
                            actual_success[r.command] += 1

                stumbles.append({
                    "task": task,
                    "first_command": first_cmd,
                    "agent_count": len(group),
                    "first_try_failure_count": first_try_failures,
                    "right_answer": right_answer,
                    "agents_eventually_used": dict(actual_success.most_common(3)),
                    "yoke_move": (
                        f"Add '{first_cmd}' as alias for '{right_answer}' — {first_try_failures}/{len(group)} agents reached for '{first_cmd}' instead of '{right_answer}'"
                    ),
                })

    return stumbles


def compute_reach_frequency(profiles: List[BehaviorProfile]) -> Dict[str, int]:
    """Total reach attempts per command (across all attempts and all agents)."""
    counter = Counter()
    for p in profiles:
        for r in p.reach_sequence:
            counter[r.command] += 1
    return dict(counter)
