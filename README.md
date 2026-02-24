# AI Debate Arena — Powered by PrysmAI

Two AIs enter. One argument wins.

Watch GPT-4o Mini and Claude Sonnet 4 debate any topic live — then see inside their responses with PrysmAI's explainability engine.

## What This Demonstrates

This is a demo app built on top of [PrysmAI](https://prysmai.manus.space) to showcase its full feature set:

- **Multi-Provider Routing** — One API key (`sk-prysm-*`) routes to both OpenAI and Anthropic based on the model name. No separate clients needed.
- **Real-Time Streaming** — Token-by-token streaming through the PrysmAI proxy with SSE (Server-Sent Events).
- **Full Observability** — Every API call is traced with latency, TTFT, token counts, and cost.
- **Confidence Analysis** — OpenAI responses get native logprobs analysis; Anthropic gets estimated confidence scoring.
- **Hallucination Detection** — Low-confidence segments are flagged as potential hallucination candidates.

## How It Works

```
User picks a topic
    ↓
GPT-4o Mini argues FOR (streaming through PrysmAI)
Claude Sonnet 4 argues AGAINST (streaming through PrysmAI)
    ↓
3 rounds: Opening → Rebuttal → Closing
    ↓
Claude judges the debate (non-streaming)
    ↓
PrysmAI dashboard shows traces, confidence heatmaps, cost comparison
```

## Quick Start

```bash
# 1. Clone and install
pip install prysmai fastapi uvicorn sse-starlette python-dotenv jinja2

# 2. Configure
echo "PRYSM_API_KEY=sk-prysm-your-key-here" > .env
echo "PRYSM_BASE_URL=https://your-prysmai-instance.com/api/v1" >> .env

# 3. Run
python app.py
# → http://localhost:8080
```

## Architecture

```
┌─────────────────────────────────────┐
│         AI Debate Arena             │
│  (FastAPI + Tailwind CSS + SSE)     │
├─────────────────────────────────────┤
│         PrysmAI Python SDK          │
│  from prysmai import PrysmClient    │
│  client = prysm.openai()            │
├─────────────────────────────────────┤
│         PrysmAI Proxy               │
│  ┌──────────┐  ┌──────────────┐     │
│  │  OpenAI   │  │  Anthropic   │    │
│  │ gpt-4o-*  │  │  claude-*    │    │
│  └──────────┘  └──────────────┘     │
├─────────────────────────────────────┤
│  Traces · Costs · Confidence · Logs │
│         PrysmAI Dashboard           │
└─────────────────────────────────────┘
```

## PrysmAI Features Exercised

| Feature | How It's Used |
|---------|---------------|
| Multi-provider routing | One `sk-prysm-*` key routes `gpt-4o-mini` → OpenAI, `claude-sonnet-4` → Anthropic |
| Streaming proxy | All debate rounds stream token-by-token through PrysmAI |
| Non-streaming proxy | Judge verdict uses synchronous call through PrysmAI |
| Trace capture | Every API call logged with full request/response |
| Latency tracking | TTFT and total latency measured per call |
| Token counting | Prompt + completion tokens tracked |
| Cost estimation | Per-call cost calculated automatically |
| Confidence analysis | OpenAI: native logprobs. Anthropic: estimated confidence |
| Hallucination detection | Low-confidence segments flagged |
| Metadata tagging | Each call tagged with app, model_key, round number |
| Context headers | X-Prysm-User-Id, X-Prysm-Session-Id, X-Prysm-Metadata |

## Files

```
app.py              — FastAPI server with SSE streaming endpoints
debate_engine.py    — Core debate logic using PrysmAI SDK
templates/index.html — Single-page frontend (Tailwind CSS)
.env                — PrysmAI credentials
README.md           — This file
```

## License

MIT — built as a demo for PrysmAI.
