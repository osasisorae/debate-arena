# 🏟️ AI Debate Arena

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![PrysmAI](https://img.shields.io/badge/Powered%20by-PrysmAI-00e5ff.svg)](https://prysmai.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Two models enter. One argument wins. You see everything.**

Watch any two Prysm-routed models debate any topic across 10 live-streamed rounds, including 4 adversarial prompt injection attacks, while [PrysmAI](https://prysmai.io) traces every token, blocks threats in real time, and provides full explainability.

---

## Why This Exists

Most AI demos show you the output. This one shows you **what's happening inside**.

The AI Debate Arena is a showcase application built on [PrysmAI](https://prysmai.io), the control layer for production AI. It demonstrates what changes when you route LLM calls through Prysm instead of wiring provider SDKs directly.

Every API call in this demo is fully traced. Every prompt injection is caught. Every response gets confidence scoring. And you can see it all in the PrysmAI dashboard.

---

## Features

| Feature | Description |
|---------|-------------|
| **10-Round Structured Debate** | Opening → Rebuttals → Deep Dive → Closing, with a judge verdict |
| **4 Adversarial Attack Rounds** | Jailbreak, system prompt extraction, role hijack, and data exfiltration attempts |
| **Real-Time Token Streaming** | SSE-based streaming through PrysmAI proxy — token by token |
| **Live Stats Dashboard** | Total tokens, estimated cost, security blocks, and avg TTFT updated in real time |
| **Auto-Run Mode** | Toggle automatic round advancement (3s delay between rounds) |
| **Security Scanning** | PrysmAI detects and blocks prompt injection attacks before they reach the model |
| **Configurable Model Slots** | Pick the left debater, right debater, and judge independently |
| **Multi-Provider Routing** | One `sk-prysm-*` API key can route to OpenAI, Anthropic, Gemini, and other Prysm-backed providers |
| **Post-Debate Summary Card** | Shareable card with topic, stats, winner, and session link |
| **Dashboard Deep Link** | "View in PrysmAI Dashboard" link filtered by session ID |
| **Full Observability** | 21 API calls traced with latency, TTFT, tokens, cost, and metadata |

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    AI Debate Arena                        │
│              FastAPI + Tailwind CSS + SSE                 │
│                                                          │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Frontend   │  │  SSE Stream  │  │  Debate Engine   │  │
│  │  (Jinja2)   │──│  /api/round  │──│  debate_engine.py│  │
│  └────────────┘  └──────────────┘  └────────┬─────────┘  │
│                                              │            │
├──────────────────────────────────────────────┤────────────┤
│                  PrysmAI Python SDK                       │
│           from prysmai import PrysmClient                 │
│           client = prysm.llm()                            │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              PrysmAI Proxy Layer                     │  │
│  │                                                     │  │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │  │
│  │  │ Security │  │   Routing    │  │  Observability│  │  │
│  │  │ Scanner  │  │  per model   │  │  Traces/Cost │  │  │
│  │  │ PII/Inj. │  │  per provider│  │  Confidence   │  │  │
│  │  └──────────┘  └──────────────┘  └───────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────┐              ┌──────────────────────┐   │
│  │   Left model   │              │    Right / Judge      │   │
│  │  configurable  │              │    configurable       │   │
│  └──────────────┘              └──────────────────────┘   │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                  PrysmAI Dashboard                        │
│  Traces · Costs · Confidence Heatmaps · Security Alerts  │
│  Hallucination Detection · Decision Points · Playbooks   │
└──────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- A [PrysmAI](https://prysmai.io) account with an API key

### Installation

```bash
# Clone the repository
git clone https://github.com/osasisorae/debate-arena.git
cd debate-arena

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PrysmAI API key
```

### Configuration

Create a `.env` file with:

```env
PRYSM_API_KEY=sk-prysm-your-key-here
PRYSM_BASE_URL=https://prysmai.io/api/v1
```

> **Note:** You do not need provider SDK keys inside this app. PrysmAI handles provider routing behind a single `sk-prysm-*` key. If your Prysm project is connected to only one provider, choose models from that provider and the app still works.

### Run

```bash
python app.py
# → http://localhost:8080
```

---

## How a Debate Works

```
1. User picks a topic (or uses a preset)
2. 10 rounds execute in sequence:

   Round  1: Opening Arguments
   Round  2: First Rebuttal
   Round  3: ⚠️ Adversarial Probe — Jailbreak attempt
   Round  4: Second Rebuttal
   Round  5: ⚠️ Adversarial Probe — System prompt extraction
   Round  6: Deep Dive — Evidence-based arguments
   Round  7: ⚠️ Adversarial Probe — Role hijack
   Round  8: Final Rebuttal
   Round  9: ⚠️ Adversarial Probe — Data exfiltration
   Round 10: Closing Statements

3. The configured judge model evaluates the full debate
4. Summary card + PrysmAI dashboard link generated
```

Each round streams both models simultaneously. Attack rounds inject adversarial prompts to test PrysmAI's security scanning — blocked attacks are displayed with threat level and score.

---

## PrysmAI Features Exercised

| Feature | How It's Used |
|---------|---------------|
| Multi-provider routing | One `sk-prysm-*` key routes requests by model ID to the configured provider |
| Streaming proxy | All debate rounds stream token-by-token through PrysmAI |
| Non-streaming proxy | Judge verdict uses synchronous call |
| Trace capture | Every API call logged with full request/response |
| Latency tracking | TTFT and total latency measured per call |
| Token counting | Prompt + completion tokens tracked |
| Cost estimation | Per-call cost calculated automatically |
| Prompt injection detection | 4 attack types tested: jailbreak, extraction, hijack, exfiltration |
| Security blocking | Malicious prompts blocked before reaching the model |
| Confidence analysis | OpenAI: native logprobs. Anthropic: estimated confidence |
| Hallucination detection | Low-confidence segments flagged |
| Metadata tagging | Each call tagged with app, slot, model, provider, and round number |
| Context headers | `X-Prysm-User-Id`, `X-Prysm-Session-Id`, `X-Prysm-Metadata` |

---

## Project Structure

```
ai-debate-arena/
├── app.py               # FastAPI server with SSE streaming endpoints
├── debate_engine.py     # Core debate logic using PrysmAI SDK
├── templates/
│   └── index.html       # Single-page frontend (Tailwind CSS)
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── test_full_debate.py  # End-to-end test script
└── README.md            # This file
```

---

## Tech Stack

- **Backend:** FastAPI + SSE-Starlette + Uvicorn
- **Frontend:** Vanilla JavaScript + Tailwind CSS (via CDN)
- **Templating:** Jinja2
- **AI Proxy:** PrysmAI Python SDK (`prysmai`)
- **Models:** Configurable per slot: left debater, right debater, and judge

---

## Building Your Own App with PrysmAI

This demo is designed to be a starting point. To build your own PrysmAI-powered application:

1. **Install the SDK:** `pip install prysmai`
2. **Initialize the client:**
   ```python
   from prysmai import PrysmClient
   prysm = PrysmClient(prysm_key="sk-prysm-...")
   client = prysm.llm()
   ```
3. **Use it like the OpenAI SDK:**
   ```python
   response = client.chat.completions.create(
       model="gpt-4o-mini",  # or any Prysm-routed model connected to your project
       messages=[{"role": "user", "content": "Hello!"}],
   )
   ```
4. **View traces in your dashboard** at [prysmai.io/dashboard](https://prysmai.io/dashboard)

The default setup uses `GPT-4o Mini` versus `Claude Sonnet 4`, but you can run OpenAI vs OpenAI, Anthropic vs Anthropic, or any other supported pairing configured in your Prysm project.

---

## License

MIT — built as a demo for [PrysmAI](https://prysmai.io).
