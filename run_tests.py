"""Test suite for mavis-erised."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/workspace/repos/mavis-erised")

from mavis_erised import (
    __version__, play_session, quick_demo,
    AGENT_PROFILES, canary,
    BehaviorProfile, Reach, zero_shot_success_rate,
    first_reach_distribution, stumble_patterns,
    YokeMove, generate_ergonomics_report, format_report_text,
)
from mavis_erised.play import (
    play_one_agent, infer_intent, is_command_useful,
    find_useful_commands, DEFAULT_TASKS, DEFAULT_TOOLS,
)
from mavis_erised.agents.zero_shot import call_agent, mock_agent_response
from mavis_erised.behavior.recorder import record_reach
from mavis_erised.yoke.adjuster import (
    propose_alias, propose_rename, propose_auto_translate,
    analyze_stumbles, save_yoke_moves,
)


results = []
failures = []


def test(name, func):
    try:
        func()
        results.append((name, "PASS"))
    except AssertionError as e:
        results.append((name, f"FAIL: {e}"))
        failures.append(name)
    except Exception as e:
        results.append((name, f"ERROR: {type(e).__name__}: {e}"))
        failures.append(name)


def t_canary():
    assert canary() == "0x24a555471370b18d"


def t_version():
    assert __version__ == "0.1.0"


def t_default_tasks():
    assert len(DEFAULT_TASKS) >= 5


def t_default_tools():
    assert len(DEFAULT_TOOLS) >= 10


def t_agent_profiles():
    assert "zai" in AGENT_PROFILES
    assert "qwen" in AGENT_PROFILES
    assert "kimi" in AGENT_PROFILES
    for voice, profile in AGENT_PROFILES.items():
        assert "model" in profile
        assert "system" in profile


def test_mock_agent_response():
    resp = mock_agent_response("zai", "show health", ["fleet health", "fleet version"])
    assert "command" in resp
    assert resp["voice"] == "zai"


def test_call_agent():
    resp = call_agent("qwen", "show fleet health",
                      ["fleet health", "fleet version"])
    assert "command" in resp
    assert resp["voice"] == "qwen"


def t_infer_intent_health():
    assert infer_intent("show me the fleet's health") == "check_status"


def t_infer_intent_run():
    assert infer_intent("run a quilt experiment") == "run_experiment"


def t_infer_intent_unknown():
    intent = infer_intent("xyzzy something something")
    assert intent == "unknown"


def t_is_command_useful_match():
    """Direct word match."""
    assert is_command_useful("health", "show me the health", ["health", "version"])


def t_is_command_useful_substring():
    """Substring match."""
    assert is_command_useful("version", "show the version number", ["health", "version"])


def t_is_command_useful_mismatch():
    """No match."""
    assert not is_command_useful("xyz", "show the version", ["version"])


def test_find_useful_commands():
    cmds = find_useful_commands("show me the fleet's health", DEFAULT_TOOLS)
    assert "fleet health" in cmds


def test_play_one_agent():
    profile = play_one_agent("zai", "show me the fleet's health", DEFAULT_TOOLS)
    assert profile.agent_id == "zai"
    assert len(profile.reach_sequence) >= 1


def test_behavior_profile_record_reach():
    p = BehaviorProfile(agent_id="test", task="x")
    record_reach(p, "health", success=True)
    assert len(p.reach_sequence) == 1
    assert p.reach_sequence[0].command == "health"
    assert p.final_success


def test_zero_shot_success_rate():
    profiles = [
        BehaviorProfile(agent_id="a", task="x"),
        BehaviorProfile(agent_id="b", task="y"),
    ]
    record_reach(profiles[0], "cmd1", success=True)
    record_reach(profiles[1], "cmd2", success=False)
    record_reach(profiles[1], "cmd1", success=True)
    rate = zero_shot_success_rate(profiles)
    assert rate == 0.5  # 1/2 succeeded on first try


def test_first_reach_distribution():
    profiles = []
    for cmd in ["health", "health", "version"]:
        p = BehaviorProfile(agent_id=f"a{cmd}", task="x")
        record_reach(p, cmd, success=True)
        profiles.append(p)
    dist = first_reach_distribution(profiles)
    assert dist["health"] == 2
    assert dist["version"] == 1


def test_stumble_patterns():
    """When agents reach for the wrong command, find patterns."""
    profiles = []
    for _ in range(3):
        p = BehaviorProfile(agent_id=f"x", task="check status")
        record_reach(p, "show", success=False)
        record_reach(p, "health", success=True)
        profiles.append(p)
    stumbles = stumble_patterns(profiles)
    assert any(s["first_command"] == "show" for s in stumbles)


def t_propose_alias():
    m = propose_alias("health", "show", 5)
    assert m.move_type == "alias"
    assert m.from_command == "show"
    assert m.to_command == "health"
    assert m.confidence > 0.5


def t_propose_rename():
    m = propose_rename("check_status", "show", 3)
    assert m.move_type == "rename"


def t_propose_auto_translate():
    m = propose_auto_translate("xyz", 2)
    assert m.move_type == "auto_translate"


def test_analyze_stumbles():
    stumbles = [{
        "task": "check status",
        "first_command": "show",
        "agent_count": 3,
        "failure_count": 2,
        "success_after": {"health": 1},
    }]
    moves = analyze_stumbles(stumbles)
    assert len(moves) == 1
    assert moves[0].from_command == "show"


def test_save_yoke_moves():
    with tempfile.TemporaryDirectory() as td:
        from pathlib import Path
        import mavis_erised.yoke.adjuster as adj_mod
        original = adj_mod.YOKE_DIR
        adj_mod.YOKE_DIR = Path(td)
        try:
            moves = [YokeMove(move_type="alias", from_command="x", to_command="y",
                               rationale="test", confidence=0.5)]
            path = save_yoke_moves(moves)
            assert path.exists()
        finally:
            adj_mod.YOKE_DIR = original


def test_generate_report():
    profiles = []
    for _ in range(3):
        p = BehaviorProfile(agent_id="a", task="check health")
        record_reach(p, "health", success=True)
        profiles.append(p)
    report = generate_ergonomics_report(profiles)
    assert report["summary"]["total_agents"] == 3
    assert report["summary"]["zero_shot_success_rate"] == 1.0


def test_format_report():
    profiles = [BehaviorProfile(agent_id="a", task="x")]
    record_reach(profiles[0], "y", success=True)
    report = generate_ergonomics_report(profiles)
    text = format_report_text(report)
    assert "ERISED ERGONOMICS REPORT" in text
    assert "Zero-shot success rate" in text


def test_quick_demo():
    result = quick_demo()
    assert "report" in result
    assert result["profiles_count"] > 0


test("test_canary", t_canary)
test("test_version", t_version)
test("test_default_tasks", t_default_tasks)
test("test_default_tools", t_default_tools)
test("test_agent_profiles", t_agent_profiles)
test("test_mock_agent_response", test_mock_agent_response)
test("test_call_agent", test_call_agent)
test("test_infer_intent_health", t_infer_intent_health)
test("test_infer_intent_run", t_infer_intent_run)
test("test_infer_intent_unknown", t_infer_intent_unknown)
test("test_is_command_useful_match", t_is_command_useful_match)
test("test_is_command_useful_substring", t_is_command_useful_substring)
test("test_is_command_useful_mismatch", t_is_command_useful_mismatch)
test("test_find_useful_commands", test_find_useful_commands)
test("test_play_one_agent", test_play_one_agent)
test("test_behavior_profile_record_reach", test_behavior_profile_record_reach)
test("test_zero_shot_success_rate", test_zero_shot_success_rate)
test("test_first_reach_distribution", test_first_reach_distribution)
test("test_stumble_patterns", test_stumble_patterns)
test("test_propose_alias", t_propose_alias)
test("test_propose_rename", t_propose_rename)
test("test_propose_auto_translate", t_propose_auto_translate)
test("test_analyze_stumbles", test_analyze_stumbles)
test("test_save_yoke_moves", test_save_yoke_moves)
test("test_generate_report", test_generate_report)
test("test_format_report", test_format_report)
test("test_quick_demo", test_quick_demo)

print("\n=== mavis-erised test results ===")
for name, status in results:
    print(f"  {status:60} {name}")

print(f"\n{len(results) - len(failures)}/{len(results)} passed")
if failures:
    sys.exit(1)
