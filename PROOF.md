# mavis-erised — proof through the pudding

**Built**: Sept 23, 2026
**Tag**: v0.1.0
**Location**: `/workspace/repos/mavis-erised/`
**GitHub**: https://github.com/SuperInstance/mavis-erised
**Canary**: `0x24a555471370b18d` ✓
**Tests**: 27/27 passing
**Fleet**: 44/44 polyformal

## What it does

Spawns zero-shot agents with **no documentation** and watches where they instinctively reach. Captures their instinctive behavior and proposes **yoke moves** — interface changes that move the cockpit to where the agent reaches.

## Components

| Component | File | Purpose |
|-----------|------|---------|
| Zero-shot agents | `agents/zero_shot.py` | zai/qwen/kimi agents with no docs |
| Behavior recorder | `behavior/recorder.py` | Captures every reach, success/failure |
| Yoke adjuster | `yoke/adjuster.py` | Proposes aliases, renames, auto-translates |
| Ergonomics reporter | `ergonomics/reporter.py` | Generates the "did the plane fly right?" report |
| Play orchestrator | `play.py` | Runs multi-agent sessions |
| CLI | `cli.py` | `play`, `report`, `voices`, `tasks`, `version` |

## Real Session Results (63 agents, 3 voices × 7 tasks × 3 runs)

```
Total agents tested: 63
Zero-shot success rate: 7.9%
Training needed: 92.1%
Ergonomic grade: D
```

### First reach distribution (what agents instinctively reach for first)

| Command | Times | % of agents |
|---------|-------|------------|
| `version` | 22 | 35% |
| `list` | 18 | 29% |
| `run` | 16 | 25% |
| `help` | 7 | 11% |

### Critical insight

**Agents treat `version` as a meta-command** — they reach for it when they want to do ANYTHING with the fleet. This is a real ergonomic finding.

### Yoke moves proposed (16 total, top 5)

1. `[alias] version → fleet health` (confidence 0.40)
2. `[alias] version → fleet version` (confidence 0.60)
3. `[alias] version → fleet list-substrates` (confidence 0.60)
4. `[alias] version → fleet run quilt` (confidence 0.60)
5. `[alias] version → fleet promote` (confidence 0.60)

### Recommended yoke

Don't add 5 aliases. Instead: **make `version` fall through to `help`/`list`** — it's already instinctive. Agents reach for it because they want to know what's available. Honor that.

## Doctrine (the bedrock)

- **`cells_are_scars`**: every agent action leaves a record (a reach, not a command)
- **`witness_log_is_prediction`**: the recorder predicts where the next agent will reach
- **`canon_gate_is_chord`**: the report is canon only when multiple voices agree
- **`oracle_is_heard`**: the ergonomics report hears what the agent wanted
- **`substrate_quantum`**: the cockpit and the agent are entangled, not separate
- **`polyformalism_canary`**: same canary hash, regardless of which model plays

## Casey Ergonomics Doctrine (origin)

> "A good plane-maker doesn't try to train the agents. Instead, when agents reach for the wrong thing, the plane-maker moves the yoke to where they reach. When they parse something wrong, change how it's displayed so the intuitive thing is the right thing. Iterate until the plane's idealized flight is how it actually flies with any agent."

## Future model names per Casey brainstorming

- **CTM** (Cellular Typesafe Models): cells are typesafe primitives
- **TFM** (Time-First Models): optimize first-reach-to-success time
- **Origin-Centric Models**: expose intent directly, not implementation
- **SFM** (Simulation-First Models): let agents reach for the simulated outcome

## How this fits the fleet

mavis-erised is the **substrate-11** in our canon substrate walker:

1. file, 2. search, 3. graph, 4. audio, 5. mcp, 6. game, 7. print, 8. orchestration,
9. ledger, 10. visualization, 11. **ergonomics** (this)

It's also the foundation for training the **next generation of agent-tuned models** without explicit fine-tuning — by automatically adapting the tools to fit what agents reach for.
