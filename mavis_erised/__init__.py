"""mavis-erised — the agent playground.

The principle (Casey's directive): don't train agents to fit the cockpit.
Move the cockpit to where the agent reaches.

This package:
1. Zero-shot agents (no docs, just try) — see agents/zero_shot.py
2. Behavior recorder (where they reach) — see behavior/recorder.py
3. Yoke adjuster (proposed moves) — see yoke/adjuster.py
4. Ergonomics reporter (the report) — see ergonomics/reporter.py
5. Play orchestrator — see play.py
"""
from .play import (
    play_session, quick_demo,
    DEFAULT_TASKS, DEFAULT_TOOLS, __version__,
)
from .agents.zero_shot import (
    call_agent, AGENT_PROFILES, canary,
)
from .behavior.recorder import (
    BehaviorProfile, Reach, zero_shot_success_rate,
    first_reach_distribution, stumble_patterns,
)
from .yoke.adjuster import (
    YokeMove, analyze_stumbles, save_yoke_moves,
)
from .ergonomics.reporter import (
    generate_ergonomics_report, format_report_text,
)


__all__ = [
    "__version__", "play_session", "quick_demo", "DEFAULT_TASKS", "DEFAULT_TOOLS",
    "AGENT_PROFILES", "canary",
    "BehaviorProfile", "Reach", "zero_shot_success_rate",
    "first_reach_distribution", "stumble_patterns",
    "YokeMove", "analyze_stumbles",
    "generate_ergonomics_report", "format_report_text",
]
