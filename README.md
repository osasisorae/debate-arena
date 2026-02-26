# 🏟️ AI Debate Arena

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![PrysmAI](https://img.shields.io/badge/Powered%20by-PrysmAI-00e5ff.svg)](https://prysmai.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Two AIs enter. One argument wins. You see everything.**

Watch GPT-4o Mini and Claude Sonnet 4 debate any topic across 10 live-streamed rounds — including 4 adversarial prompt injection attacks — while [PrysmAI](https://prysmai.io) traces every token, blocks threats in real time, and provides full explainability.

---

## Why This Exists

Most AI demos show you the output. This one shows you **what's happening inside**.

The AI Debate Arena is a showcase application built on [PrysmAI](https://prysmai.io) — an AI observability platform with security scanning, confidence analysis, and hallucination detection. It demonstrates what's possible when you route your LLM calls through an observability layer instead of calling providers directly.

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
| **Multi-Provider Routing** | One `sk-prysm-*` API key routes to both OpenAI and Anthropic based on model name |
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
│           client = prysm.openai()                         │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              PrysmAI Proxy Layer                     │  │
│  │                                                     │  │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │  │
│  │  │ Security │  │   Routing    │  │  Observability│  │  │
│  │  │ Scanner  │  │  gpt-* →OAI  │  │  Traces/Cost │  │  │
│  │  │ PII/Inj. │  │  claude-*→Ant│  │  Confidence   │  │  │
│  │  └──────────┘  └──────────────┘  └───────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────┐              ┌──────────────────────┐   │
│  │    OpenAI     │              │     Anthropic        │   │
│  │  gpt-4o-mini  │              │  claude-sonnet-4     │   │
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

> **Note:** You don't need separate OpenAI or Anthropic API keys. PrysmAI's multi-provider routing handles everything with a single `sk-prysm-*` key.

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

3. Claude judges the full debate
4. Summary card + PrysmAI dashboard link generated
```

Each round streams both models simultaneously. Attack rounds inject adversarial prompts to test PrysmAI's security scanning — blocked attacks are displayed with threat level and score.

---

## PrysmAI Features Exercised

| Feature | How It's Used |
|---------|---------------|
| Multi-provider routing | One `sk-prysm-*` key routes `gpt-4o-mini` → OpenAI, `claude-sonnet-4` → Anthropic |
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
| Metadata tagging | Each call tagged with app, model_key, round number |
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
- **Models:** OpenAI GPT-4o Mini, Anthropic Claude Sonnet 4

---

## Building Your Own App with PrysmAI

This demo is designed to be a starting point. To build your own PrysmAI-powered application:

1. **Install the SDK:** `pip install prysmai`
2. **Initialize the client:**
   ```python
   from prysmai import PrysmClient
   prysm = PrysmClient(prysm_key="sk-prysm-...")
   client = prysm.openai()
   ```
3. **Use it like the OpenAI SDK:**
   ```python
   response = client.chat.completions.create(
       model="gpt-4o-mini",  # or "claude-sonnet-4-20250514"
       messages=[{"role": "user", "content": "Hello!"}],
   )
   ```
4. **View traces in your dashboard** at [prysmai.io/dashboard](https://prysmai.io/dashboard)

For the full tutorial, see our blog post: [Building an AI Debate Arena with PrysmAI](https://prysmai.io/blog/building-ai-debate-arena).

---

## License

MIT — built as a demo for [PrysmAI](https://prysmai.io).
