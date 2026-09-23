"""Zero-shot agents — agents that pilot our tools with no instructions.

The hypothesis (Casey's directive): don't train the agent; watch where
the agent instinctively reaches. Then move the yoke to where they reach.

A zero-shot agent:
- Sees a list of available tools (CLI commands)
- Has a task
- Has no documentation, no examples, no help
- Tries to use the tools based on name intuition alone
- We record every action they take
"""
import json
import os
import random
import re
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


ERISED_BASE = Path("/workspace/research/mavis-erised")
ERISED_BASE.mkdir(parents=True, exist_ok=True)


@dataclass
class AgentAction:
    """A single action an agent takes."""
    agent_id: str
    timestamp: str
    command: str
    args: List[str]
    kwargs: Dict
    intent: str  # what we think they were trying to do
    success: bool
    output_preview: str


def fnv1a_64(s: str) -> int:
    h = 0xcbf29ce484222325
    for b in s.encode("utf-8"):
        h = h ^ b
        h = (h * 0x100000001b3) & 0xffffffffffffffff
    return h


def canary() -> str:
    return f"0x{fnv1a_64('café Δ 日本語'):016x}"


# ─── Zero-shot agent profiles ───────────────────────────────

AGENT_PROFILES = {
    "zai": {
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "voice": "zai",
        "system": "You are a zero-shot agent with no instructions. Use the tools available based on what their names suggest. When in doubt, reach for what feels right.",
        "language_style": "literal",
    },
    "qwen": {
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "voice": "qwen",
        "system": "You are a zero-shot agent. Pick the most intuitive tool. Don't read docs — just try.",
        "language_style": "concise",
    },
    "kimi": {
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "voice": "kimi",
        "system": "You are a zero-shot agent. Reach for what you think is right.",
        "language_style": "exploratory",
    },
}


def call_agent(voice: str, task: str, available_tools: List[str],
               use_real_api: bool = False) -> Dict:
    """Call a zero-shot agent with a task. Returns what they chose to do."""
    profile = AGENT_PROFILES[voice]

    # Build the prompt the agent sees
    tools_list = "\n".join(f"- {t}" for t in available_tools)
    prompt = f"""Available tools (no docs — figure it out from names):
{tools_list}

Your task: {task}

Respond with a single shell command using one of these tools. Be concise."""

    if use_real_api:
        # Use real LLM
        api_key = os.environ.get("DEEPINFRA_TOKEN") or os.environ.get("DEEPINFRA_API_KEY")
        if api_key:
            try:
                body = json.dumps({
                    "messages": [
                        {"role": "system", "content": profile["system"]},
                        {"role": "user", "content": prompt},
                    ],
                    "model": profile["model"],
                    "max_tokens": 200,
                    "temperature": 0.7,
                }).encode()

                endpoints = [
                    "https://api.deepinfra.com/v1/openai/chat/completions",
                    "https://api.deepinfra.com/v1/chat/completions",
                ]
                for url in endpoints:
                    try:
                        req = urllib.request.Request(
                            url,
                            data=body,
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                            },
                        )
                        with urllib.request.urlopen(req, timeout=60) as resp:
                            data = json.loads(resp.read())
                        return {
                            "voice": voice,
                            "command": data["choices"][0]["message"]["content"].strip(),
                            "raw_response": data["choices"][0]["message"]["content"],
                            "real_api": True,
                        }
                    except Exception:
                        continue
            except Exception as e:
                pass

    # Mock: deterministic behavior based on voice style
    return mock_agent_response(voice, task, available_tools)


def mock_agent_response(voice: str, task: str, tools: List[str]) -> Dict:
    """Mock agent response — simulates what an LLM would reach for."""
    style = AGENT_PROFILES[voice]["language_style"]

    # Each voice has different instincts:
    if voice == "zai":
        # Tends to read status first, then act
        if "status" in str(tools):
            cmd = f"health"
        elif "version" in str(tools):
            cmd = f"version"
        else:
            cmd = f"health"
    elif voice == "qwen":
        # Tends to dive in directly
        if "run" in str(tools):
            cmd = f"run quilt"
        elif "add" in str(tools):
            cmd = f"add x"
        else:
            cmd = f"health"
    elif voice == "kimi":
        # Explores with show/list first
        if "list" in str(tools):
            cmd = f"list"
        elif "show" in str(tools):
            cmd = f"show"
        else:
            cmd = f"health"

    # Add some randomness
    if random.random() < 0.2:
        cmd = random.choice(["version", "help", "list"]).split()[0]

    return {
        "voice": voice,
        "command": cmd,
        "raw_response": f"<{voice} zero-shot response: {cmd}>",
        "real_api": False,
    }


# ─── Action recording ──────────────────────────────────────

def record_action(agent_id: str, command: str, intent: str = "",
                  success: bool = True, output_preview: str = "") -> AgentAction:
    """Record an agent's action."""
    from datetime import datetime
    parts = command.split()
    return AgentAction(
        agent_id=agent_id,
        timestamp=datetime.utcnow().isoformat() + "Z",
        command=parts[0] if parts else command,
        args=parts[1:] if len(parts) > 1 else [],
        kwargs={},
        intent=intent,
        success=success,
        output_preview=output_preview[:200],
    )


def save_session(agent_id: str, actions: List[AgentAction]) -> Path:
    """Save a session's actions to disk."""
    session_dir = ERISED_BASE / "sessions"
    session_dir.mkdir(exist_ok=True)
    session_file = session_dir / f"{agent_id}.jsonl"
    with session_file.open("a") as f:
        for a in actions:
            f.write(json.dumps(a.__dict__) + "\n")
    return session_file
