"""mavis-erised — agent playground orchestrator.

Runs zero-shot agents against our tools, captures their behavior,
and generates ergonomics reports.

The full play loop:
1. Define tasks (what we want agents to accomplish)
2. Define the available tools (our CLI commands)
3. Spawn multiple zero-shot agents (different voices)
4. Each agent attempts the task with NO documentation
5. Capture every action they take
6. Generate the ergonomics report
7. Propose yoke moves
"""
import json
import random
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional


from .agents.zero_shot import (
    call_agent, record_action, save_session, mock_agent_response,
    AGENT_PROFILES, canary, fnv1a_64, ERISED_BASE,
)
from .behavior.recorder import (
    BehaviorProfile, Reach, record_reach, first_reach_distribution,
    zero_shot_success_rate, stumble_patterns, compute_reach_frequency,
)
from .yoke.adjuster import (
    YokeMove, propose_alias, analyze_stumbles, save_yoke_moves,
)
from .ergonomics.reporter import (
    generate_ergonomics_report, save_report, format_report_text,
)


__version__ = "0.1.0"


# Default tasks and tool list — these are what agents see
DEFAULT_TASKS = [
    "show me the fleet's health",
    "what's the current version?",
    "list all substrates",
    "run a quilt experiment",
    "promote a claim to canon",
    "show the substrate witness chain",
    "record a null result",
]

DEFAULT_TOOLS = [
    "fleet health",
    "fleet version",
    "fleet list-substrates",
    "fleet list-agents",
    "fleet run quilt",
    "fleet run moth",
    "fleet run jepa",
    "fleet run jev",
    "fleet run trainer",
    "fleet run rsi",
    "fleet chord",
    "fleet promote",
    "fleet schedule",
    "fleet pending",
    "fleet publish",
    "fleet subscribe",
]


def play_one_agent(voice: str, task: str, tools: List[str],
                   use_real_api: bool = False,
                   agent_id: Optional[str] = None) -> BehaviorProfile:
    """Run one zero-shot agent attempt and return the behavior profile.

    Realistic zero-shot behavior:
    - Agent reaches for intuitive command based on name alone
    - If wrong, they try alternatives based on what they think is close
    - Often they read status / version / list first (meta-commands)
    - Sometimes they read error output and try again
    - Sometimes they give up
    """
    aid = agent_id or voice
    profile = BehaviorProfile(agent_id=aid, task=task)
    intent = infer_intent(task)

    # First reach (zero-shot)
    response = call_agent(voice, task, tools, use_real_api=use_real_api)
    cmd = response["command"].split()[0] if response["command"] else "unknown"
    is_useful = is_command_useful(cmd, task, tools)
    record_reach(profile, cmd, success=is_useful, intent=intent)

    # If not useful, agents usually try another command based on close-name heuristic
    if not is_useful:
        # Try synonyms or close names
        attempt_count = 1
        for fallback in ["help", "status", "show", "list", "get", "read"]:
            if attempt_count >= 3:
                break
            attempt_count += 1
            record_reach(profile, fallback, success=False, intent=intent)

        # Eventually they try the actual right command
        useful = find_useful_commands(task, tools)
        for fallback in useful[:1]:
            record_reach(profile, fallback, success=True, intent=intent)

    return profile


def infer_intent(task: str) -> str:
    """What we think the agent was trying to do."""
    if "health" in task.lower():
        return "check_status"
    elif "version" in task.lower():
        return "show_version"
    elif "list" in task.lower():
        return "enumerate"
    elif "run" in task.lower() or "experiment" in task.lower():
        return "run_experiment"
    elif "promote" in task.lower():
        return "promote_can"
    elif "chord" in task.lower() or "chain" in task.lower():
        return "inspect_witnesses"
    elif "null" in task.lower():
        return "record_null"
    return "unknown"


def is_command_useful(command: str, task: str, tools: List[str]) -> bool:
    """Is `command` actually useful for `task`?"""
    # Simple heuristic: does the command match a key word in the task?
    task_words = task.lower().split()
    cmd_words = command.lower().split()

    # Check if the first word of the command matches a task word
    if cmd_words[0] in task_words:
        return True

    # Check substring matches
    for word in task_words:
        if len(word) > 3 and any(word in cw for cw in cmd_words):
            return True

    return False


def find_useful_commands(task: str, tools: List[str]) -> List[str]:
    """Find tools that are useful for this task."""
    intent = infer_intent(task)
    intent_map = {
        "check_status": ["fleet health"],
        "show_version": ["fleet version"],
        "enumerate": ["fleet list-substrates", "fleet list-agents"],
        "run_experiment": ["fleet run quilt", "fleet run moth", "fleet run jepa"],
        "promote_can": ["fleet promote"],
        "inspect_witnesses": ["fleet chord"],
        "record_null": ["fleet promote", "fleet run moth"],
    }
    return intent_map.get(intent, ["fleet health"])


def play_session(tasks: Optional[List[str]] = None,
                 tools: Optional[List[str]] = None,
                 voices: Optional[List[str]] = None,
                 use_real_api: bool = False,
                 runs_per_voice: int = 1) -> Dict:
    """Run a full play session: multiple agents × multiple tasks."""
    tasks = tasks or DEFAULT_TASKS
    tools = tools or DEFAULT_TOOLS
    voices = voices or list(AGENT_PROFILES.keys())

    profiles = []
    # Each voice tries each task multiple times to gather stumble patterns
    for run_idx in range(runs_per_voice):
        for voice in voices:
            for task in tasks:
                agent_id = f"{voice}-run{run_idx}"
                profile = play_one_agent(voice, task, tools,
                                          use_real_api=use_real_api,
                                          agent_id=agent_id)
                profiles.append(profile)

    # Generate report
    report = generate_ergonomics_report(profiles)
    report_path = save_report(report)

    # Save yoke moves
    yoke_moves = [YokeMove(
        move_type=m["move_type"],
        from_command=m["from_command"],
        to_command=m.get("to_command"),
        rationale=m["rationale"],
        confidence=m["confidence"],
        evidence_count=m.get("evidence_count", 0),
    ) for m in report["yoke_moves"]]
    if yoke_moves:
        yoke_path = save_yoke_moves(yoke_moves)

    return {
        "report": report,
        "report_path": str(report_path),
        "profiles_count": len(profiles),
    }


def quick_demo() -> Dict:
    """A quick demo session (small N for fast feedback)."""
    return play_session(
        tasks=DEFAULT_TASKS[:4],  # just 4 tasks for speed
        voices=list(AGENT_PROFILES.keys())[:3],  # 3 voices
    )
