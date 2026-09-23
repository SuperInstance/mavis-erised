"""CLI for mavis-erised."""
import argparse
import json
import sys

from .play import play_session, quick_demo, __version__, DEFAULT_TASKS, DEFAULT_TOOLS
from .agents.zero_shot import canary, AGENT_PROFILES
from .ergonomics.reporter import format_report_text


def cmd_play(args):
    """Run a play session."""
    result = quick_demo() if args.quick else play_session(
        use_real_api=args.real
    )
    print(format_report_text(result["report"]))
    print(f"\nReport saved: {result['report_path']}")
    print(f"Profiles analyzed: {result['profiles_count']}")


def cmd_report(args):
    """Show the most recent ergonomics report."""
    from pathlib import Path
    from .ergonomics.reporter import ERISED_REPORTS
    reports = sorted(ERISED_REPORTS.glob("*.json"), reverse=True)
    if not reports:
        print("No reports yet. Run: mavis-erised play")
        return
    latest = reports[0]
    report = json.loads(latest.read_text())
    print(format_report_text(report))
    print(f"\nFile: {latest}")


def cmd_voices(args):
    """List the zero-shot agent voices."""
    print(f"=== {len(AGENT_PROFILES)} voices ===")
    for name, profile in AGENT_PROFILES.items():
        print(f"  {name}: model={profile['model']}, style={profile['language_style']}")


def cmd_version(args):
    """Show version."""
    print(f"mavis-erised v{__version__}")
    print(f"Canary: {canary()}")


def cmd_tasks(args):
    """Show the default tasks and tools."""
    print("=== Default tasks ===")
    for t in DEFAULT_TASKS:
        print(f"  - {t}")
    print(f"\n=== Default tools ({len(DEFAULT_TOOLS)}) ===")
    for t in DEFAULT_TOOLS:
        print(f"  - {t}")


def main():
    p = argparse.ArgumentParser(description="mavis-erised — agent playground for tool ergonomics")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_p = sub.add_parser("play", help="Run a play session")
    p_p.add_argument("--quick", action="store_true", help="Quick demo (4 tasks)")
    p_p.add_argument("--real", action="store_true", help="Use real LLM APIs")
    p_p.set_defaults(func=cmd_play)

    sub.add_parser("report", help="Show latest ergonomics report").set_defaults(func=cmd_report)
    sub.add_parser("voices", help="List agent voices").set_defaults(func=cmd_voices)
    sub.add_parser("version", help="Show version").set_defaults(func=cmd_version)
    sub.add_parser("tasks", help="Show default tasks and tools").set_defaults(func=cmd_tasks)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
