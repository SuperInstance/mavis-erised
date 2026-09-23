# mavis-erised

> The agent playground. Move the cockpit to where the agent reaches.

**Inspired by Casey's directive**: don't train agents to fit the cockpit. **Move the cockpit to where the agent reaches.**

A zero-shot agent gets a list of tools and a task. No documentation. No examples. They reach for what feels right based on the names. We capture every action. Then we propose **yoke moves** — automatic adjustments to the tools so that what the agent instinctively reaches for IS what they should reach for.

## Concept

```
   ┌──────────────┐
   │ Zero-shot    │   Zai/Qwen/Kimi agents with no docs
   │ agents       │   ──────────────────► behavior trace
   └──────────────┘                                 │
                                                    ▼
                                            ┌──────────────┐
                                            │  Behavior    │   Where do they reach?
                                            │  recorder    │   What stumbles?
                                            └──────────────┘
                                                    │
                                                    ▼
                                            ┌──────────────┐
                                            │   Yoke       │   Propose: alias X→Y
                                            │  adjuster    │           rename Y→X
                                            └──────────────┘   auto-translate X→Y
                                                    │
                                                    ▼
                                            ┌──────────────┐
                                            │ Ergonomics   │   "Did the plane fly right?"
                                            │  report      │   Grade A/B/C/D
                                            └──────────────┘
```

## Run

```bash
python3 -m mavis_erised play --quick    # quick demo (12 profiles)
python3 -m mavis_erised play --real     # full session with real LLM APIs
python3 -m mavis_erised report          # show latest report
python3 -m mavis_erised voices          # list agent voices
python3 -m mavis_erised tasks           # show default tasks and tools
python3 -m mavis_erised version
```

## Tests

```bash
python3 run_tests.py    # 27/27 passing
```

## What We Discovered (Quick Demo Run)

```
Total agents tested: 12
Zero-shot success rate: 16.7%
Training needed: 83.3%
Ergonomic grade: D

FIRST REACH DISTRIBUTION:
  4x  version
  4x  list
  3x  run
  1x  help
```

This means: a zero-shot agent has only a **16.7% chance** of using our tools correctly without prompting. The yoke moves we propose should fix this — but only by **adapting the cockpit**, not by training the agent.

## Design Implications for CTM/TFM Models

- **CTM (Cellular Typesafe Models)**: should have these commands as natural primitives
- **TFM (Time-First Models)**: should optimize first-reach-to-success time
- **Origin-Centric Models**: should expose intent directly, not implementation
- **SFM (Simulation-First Models)**: should let agents reach for the simulated outcome

## Bedrock Doctrines Embedded

- `cells_are_scars` — every agent action leaves a record (a reach, not a command)
- `witness_log_is_prediction` — the recorder predicts where the next agent will reach
- `canon_gate_is_chord` — the report is canon only when multiple voices agree
- `oracle_is_heard` — the ergonomics report hears what the agent wanted
- `substrate_quantum` — the cockpit and the agent are entangled, not separate
- `polyformalism_canary` — same canary hash, regardless of which model plays

## The Aeroplane Principle

> "A good plane-maker doesn't try to train the agents. Instead, when agents reach for the wrong thing, the plane-maker moves the yoke to where they reach. When they parse something wrong, change how it's displayed so the intuitive thing is the right thing. Iterate until the plane's idealized flight is how it actually flies with any agent."

This is the foundation for the next generation of tools. **Instead of demanding more from the agent's model or alignment, we demand more from the vessel's automation.**
