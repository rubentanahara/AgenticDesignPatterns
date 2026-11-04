# Agentic Design Patterns: Study Notes

Notes and runnable code for Antonio Gulli's *Agentic Design Patterns* (the book itself is not included: it is copyrighted, buy it from the publisher). There is one folder per chapter. Each `README.md` has: summary, problem and when to use it, key takeaways, non-obvious details, and a worked example that points to the code.

| # | Chapter | One-line takeaway |
|---|---------|-------------------|
| 01 | [Prompt Chaining](01-prompt-chaining/README.md) | Split one hard prompt into focused steps with structured handoffs, and validate between them. |
| 02 | [Routing](02-routing/README.md) | Classify first, then dispatch. Cheap rules before the LLM, and always a fallback route. |
| 03 | [Parallelization](03-parallelization/README.md) | Fan out independent work and fan in with a grounded synthesizer. Latency becomes the slowest branch, not the sum. |
| 04 | [Reflection](04-reflection/README.md) | A separate critic with the original task and a structured verdict, in a loop with a round cap. |
| 05 | [Tool Use](05-tool-use/README.md) | The model only proposes calls. Your code executes, validates, returns errors as observations, and bounds the loop. |
| 06 | [Planning](06-planning/README.md) | Plan only when the *how* must be discovered. Otherwise use a fixed workflow. |
| 07 | [Multi-Agent Collaboration](07-multi-agent-collaboration/README.md) | Topology is the key decision. Transfer hands off control, agent-as-tool keeps it. |
| 08 | [Memory Management](08-memory-management/README.md) | Context window = short-term memory, external store + retrieval = long-term. Write state only through events. |
| 09 | [Learning and Adaptation](09-learning-and-adaptation/README.md) | Propose, evaluate automatically, keep the best, repeat. The evaluator is the whole game. |
| 10 | [Model Context Protocol](10-model-context-protocol/README.md) | A standard client-server protocol for tools, resources, and prompts. It won't fix an agent-hostile API. |
| 11 | [Goal Setting and Monitoring](11-goal-setting-and-monitoring/README.md) | SMART goals with per-goal verdicts. Prefer deterministic monitors, and escalate when the budget runs out. |
| 12 | [Exception Handling and Recovery](12-exception-handling-and-recovery/README.md) | Retry transient errors, fall back on permanent ones, label degraded results, escalate when all else fails. |
| 13 | [Human-in-the-Loop](13-human-in-the-loop/README.md) | Put the human gate right before irreversible actions. Policies (human-on-the-loop) scale, reviews don't. |
| 14 | [Knowledge Retrieval (RAG)](14-knowledge-retrieval-rag/README.md) | Retrieve, augment, generate. Metadata lets the agent resolve conflicts, and "I don't know" must be allowed. |
| 15 | [Inter-Agent Communication (A2A)](15-inter-agent-communication-a2a/README.md) | Agent Cards plus JSON-RPC tasks let opaque agents from any framework delegate to each other. |
| 16 | [Resource-Aware Optimization](16-resource-aware-optimization/README.md) | A cheap triage picks the model by difficulty and remaining budget. Bill the model that actually ran. |
| 17 | [Reasoning Techniques](17-reasoning-techniques/README.md) | More inference-time compute (CoT, voting, PAL, ReAct) can beat a bigger model. Verify instead of trusting the chain. |
| 18 | [Guardrails / Safety](18-guardrails-safety/README.md) | Defense in depth: deny-lists, a cheap LLM guard, tool-argument checks against trusted state, least privilege. |
| 19 | [Evaluation and Monitoring](19-evaluation-and-monitoring/README.md) | Score both the final answer and the trajectory. Mix automated metrics, LLM judges, and humans. |
| 20 | [Prioritization](20-prioritization/README.md) | The LLM rates tasks, code ranks the ready ones with explicit weights, and new events re-rank. |
| 21 | [Exploration and Discovery](21-exploration-and-discovery/README.md) | Generate diverse hypotheses, rank them with pairwise Elo debates, evolve the winner, keep a human in the loop. |
| 22 | [Appendix A: Advanced Prompting](22-appendix-a-advanced-prompting-techniques/README.md) | Clear verbs, positive instructions, mixed-class few-shot, delimiters, and Pydantic-parsed structured output. |
| 23 | [Appendix B: GUI and Real-World Agents](23-appendix-b-gui-and-real-world-agents/README.md) | Perceive, interpret, act, re-observe. Use a GUI only when no API exists, and sandbox it. |
| 24 | [Appendix G: Coding Agents](24-appendix-g-coding-agents/README.md) | The human orchestrates curated context and specialist personas. Prompts are versioned code. Review runs on pre-commit. |

## Appendices not turned into chapters

- **C, Quick overview of agentic frameworks.** A reference comparison of LangChain, LangGraph, ADK, CrewAI, and others. It has no pattern of its own, and the frameworks are used throughout the chapters.
- **D, Building an agent with AgentSpace.** A product walkthrough.
- **E, AI agents on the CLI.** A product survey of CLI coding agents. The pattern content is covered in Appendix G.
- **F, Under the hood: reasoning engines.** Mostly models' own descriptions of how they reason. The techniques are covered in Ch 17.

## Running the code

- **Stack:** the book's own, Google ADK and LangChain/LangGraph on Gemini. One root `requirements.txt` covers every chapter.
- **API key:** `export GOOGLE_API_KEY=...` (Gemini API). See [Getting an API key](#getting-an-api-key).
- **Models:** model names are a `MODEL` constant at the top of each file. Change them there when models are retired.
- **Verified with:** Python 3.12, langchain 1.4.7, google-adk 2.13.0, MCP SDK 2.3.0. Every script was import-checked. The deterministic parts (assertions, MCP discovery, A2A agent card, ADK state scopes) were run without an API key. LLM calls were not run, because no key was available while writing.
- **Offline-runnable without a key:** `08-memory-management/state_scopes_adk.py`, `10-model-context-protocol/discover.py`, `19-evaluation-and-monitoring/trajectory_metrics.py`.

### Quick start

All chapters share the same dependencies, so one environment covers them all. Keep it outside this folder: the repo lives in iCloud, and an in-repo `.venv` would sync thousands of files.

```bash
uv venv ~/.venvs/adp --python 3.12
source ~/.venvs/adp/bin/activate
uv pip install langchain-core langchain-google-genai langgraph pydantic rich uvicorn "google-adk[mcp,a2a]"
export GOOGLE_API_KEY=...
```

### Getting an API key

1. Open [Google AI Studio](https://aistudio.google.com/apikey) and sign in with a Google account.
2. Click **Create API key**, then pick an existing Google Cloud project or let it create one.
3. Copy the key and add `export GOOGLE_API_KEY=your-key` to `~/.zshrc` so every new terminal has it.

Never put the key in a file inside this folder: iCloud syncs it along with the notes. The free tier is enough for these scripts, but it has per-minute rate limits. Fan-out chapters such as 03 and 21 can hit them. If a script fails with a 429 error, wait a minute and retry.

### Running a chapter with the helper

The `Makefile` in the repo root runs any chapter by number:

```bash
make run CH=01
make run CH=02 FILE=router.py
```

- `FILE=` is needed only when a chapter has more than one script. If you leave it out, the helper lists the choices.
- It uses `~/.venvs/adp/bin/python` when that environment exists, so there is no need to activate it. Otherwise it falls back to `python3`. Override with `PYTHON=/path/to/python`.
- It stops with a short message when `CH` is missing, no folder matches, or the chapter has no scripts (chapter 23).
- `PYTHONPATH=. python 01-prompt-chaining/chain.py` works too. `PYTHONPATH=.` lets scripts import the shared `step_logger.py` at the repo root. Every script shows its pattern phases with `rich`, which is part of the shared install above. `step_logger.py` provides `phase` (stage rule), `show` (value panel), `show_event` (ADK tool calls, results, and answers), and `StepLogger().step` (LCEL tap).

Chapters with extra steps:

- **15 (A2A):** start `python 15-inter-agent-communication-a2a/weather_server.py` in one terminal, then run `python 15-inter-agent-communication-a2a/trip_planner_client.py` in another.
- **24 (Coding Agents):** `review_staged.py` reviews staged changes, so run it inside a git repo after `git add -p`.
