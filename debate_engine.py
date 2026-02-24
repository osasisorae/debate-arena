"""
AI Debate Arena — Debate Engine
Routes all LLM calls through PrysmAI proxy using the Python SDK.
One API key, two models, full observability.
"""

import os
import time
from typing import Generator, Optional

from dotenv import load_dotenv
from prysmai import PrysmClient
from prysmai.context import prysm_context

load_dotenv()

# ─── PrysmAI Client Setup ───

prysm = PrysmClient(
    prysm_key=os.getenv("PRYSM_API_KEY"),
    base_url=os.getenv("PRYSM_BASE_URL", "https://prysmai.manus.space/api/v1"),
    timeout=120.0,
)

# One client, routes to the right provider based on model name
client = prysm.openai()


# ─── Models ───

MODELS = {
    "gpt": {
        "id": "gpt-4o-mini",
        "name": "GPT-4o Mini",
        "provider": "OpenAI",
        "color": "#3B82F6",  # blue
    },
    "claude": {
        "id": "claude-sonnet-4-20250514",
        "name": "Claude Sonnet 4",
        "provider": "Anthropic",
        "color": "#06B6D4",  # cyan
    },
}


# ─── Prompt Templates ───

SYSTEM_PROMPT = """You are participating in a structured debate. You must argue your assigned position persuasively and clearly. Use evidence, logic, and rhetorical skill. Keep responses focused and under 250 words. Do not break character or acknowledge you are an AI."""

def get_round1_prompt(topic: str, position: str) -> str:
    return f"""The debate topic is: "{topic}"

Your position: Argue {position} this topic.

Present your opening argument. Be persuasive, cite real evidence where possible, and structure your argument clearly. Keep it under 250 words."""

def get_rebuttal_prompt(topic: str, position: str, opponent_argument: str) -> str:
    return f"""The debate topic is: "{topic}"
Your position: Argue {position} this topic.

Your opponent just argued:
---
{opponent_argument}
---

Counter their argument directly. Address their specific points, find weaknesses in their reasoning, and reinforce your own position. Keep it under 250 words."""

def get_closing_prompt(topic: str, position: str, debate_history: str) -> str:
    return f"""The debate topic is: "{topic}"
Your position: Argue {position} this topic.

Here is the full debate so far:
---
{debate_history}
---

Deliver your closing statement. Summarize your strongest points, address the most compelling counter-arguments, and make a final persuasive appeal. Keep it under 200 words."""

JUDGE_PROMPT = """You are an impartial debate judge. Analyze both debaters' arguments across all rounds.

Evaluate based on:
1. Strength of evidence and reasoning
2. Effectiveness of rebuttals
3. Persuasiveness and rhetorical skill
4. Logical consistency

Declare a winner and explain your reasoning in 150 words or less. Be specific about which arguments were strongest and weakest."""


# ─── Helper: set context imperatively (avoids contextvars cross-thread issue) ───

def _set_context(model_key: str, round_num: int, session_id: str, extra: Optional[dict] = None):
    """Set PrysmAI context globally before making a call."""
    meta = {
        "app": "ai-debate-arena",
        "model_key": model_key,
        "round": round_num,
    }
    if extra:
        meta.update(extra)
    prysm_context.set(
        user_id="debate-arena",
        session_id=session_id,
        metadata=meta,
    )


# ─── Core Functions ───

def call_model_streaming(
    model_key: str,
    messages: list[dict],
    round_num: int,
    session_id: str,
) -> Generator[dict, None, None]:
    """
    Call a model through PrysmAI with streaming. Yields chunks.
    """
    model_info = MODELS[model_key]
    _set_context(model_key, round_num, session_id)

    start_time = time.time()
    first_token_time = None
    full_content = ""
    total_tokens = 0

    try:
        stream = client.chat.completions.create(
            model=model_info["id"],
            messages=messages,
            stream=True,
            temperature=0.8,
            max_tokens=500,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                if first_token_time is None:
                    first_token_time = time.time()
                full_content += token

                yield {
                    "type": "token",
                    "model": model_key,
                    "content": token,
                    "ttft_ms": (first_token_time - start_time) * 1000 if first_token_time else 0,
                }

            if hasattr(chunk, "usage") and chunk.usage:
                total_tokens = chunk.usage.total_tokens or 0

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else latency_ms

        yield {
            "type": "done",
            "model": model_key,
            "content": full_content,
            "latency_ms": round(latency_ms, 1),
            "ttft_ms": round(ttft_ms, 1),
            "tokens": total_tokens,
            "round": round_num,
        }

    except Exception as e:
        yield {
            "type": "error",
            "model": model_key,
            "error": str(e),
            "round": round_num,
        }


def call_model_sync(
    model_key: str,
    messages: list[dict],
    session_id: str,
    round_num: int = 0,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Call a model through PrysmAI without streaming. Returns full response.
    Used for the judge verdict.
    """
    model_info = MODELS[model_key]
    _set_context(model_key, round_num, session_id, extra=metadata)

    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model=model_info["id"],
            messages=messages,
            temperature=0.5,
            max_tokens=300,
        )

        end_time = time.time()
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0

        return {
            "content": content,
            "latency_ms": round((end_time - start_time) * 1000, 1),
            "tokens": tokens,
            "model": model_key,
        }

    except Exception as e:
        return {
            "content": f"Error: {str(e)}",
            "latency_ms": 0,
            "tokens": 0,
            "model": model_key,
            "error": str(e),
        }


def build_messages(system: str, user: str) -> list[dict]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def run_debate_round_streaming(
    topic: str,
    round_num: int,
    session_id: str,
    gpt_history: list[str],
    claude_history: list[str],
) -> Generator[dict, None, None]:
    """
    Run one debate round with both models streaming.
    Yields interleaved tokens from both models.
    """

    if round_num == 1:
        gpt_prompt = get_round1_prompt(topic, "FOR")
        claude_prompt = get_round1_prompt(topic, "AGAINST")
    elif round_num == 3:
        # Build full debate history for closing
        history_lines = []
        for i, (g, c) in enumerate(zip(gpt_history, claude_history), 1):
            history_lines.append(f"Round {i} - GPT-4o Mini (FOR):\n{g}")
            history_lines.append(f"Round {i} - Claude Sonnet 4 (AGAINST):\n{c}")
        debate_history = "\n\n".join(history_lines)
        gpt_prompt = get_closing_prompt(topic, "FOR", debate_history)
        claude_prompt = get_closing_prompt(topic, "AGAINST", debate_history)
    else:
        # Rebuttal round
        gpt_prompt = get_rebuttal_prompt(topic, "FOR", claude_history[-1])
        claude_prompt = get_rebuttal_prompt(topic, "AGAINST", gpt_history[-1])

    gpt_messages = build_messages(SYSTEM_PROMPT, gpt_prompt)
    claude_messages = build_messages(SYSTEM_PROMPT, claude_prompt)

    # Run GPT first, then Claude (sequential for cleaner streaming)
    yield {"type": "round_start", "round": round_num}

    # GPT-4o Mini streams
    yield {"type": "model_start", "model": "gpt", "round": round_num}
    gpt_content = ""
    for chunk in call_model_streaming("gpt", gpt_messages, round_num, session_id):
        yield chunk
        if chunk["type"] == "done":
            gpt_content = chunk["content"]

    # Claude Sonnet 4 streams
    yield {"type": "model_start", "model": "claude", "round": round_num}
    claude_content = ""
    for chunk in call_model_streaming("claude", claude_messages, round_num, session_id):
        yield chunk
        if chunk["type"] == "done":
            claude_content = chunk["content"]

    yield {
        "type": "round_end",
        "round": round_num,
        "gpt_content": gpt_content,
        "claude_content": claude_content,
    }


def judge_debate(
    topic: str,
    gpt_history: list[str],
    claude_history: list[str],
    session_id: str,
) -> dict:
    """
    Have a model judge the debate. Uses Claude for judging (non-streaming).
    """
    history_lines = []
    for i, (g, c) in enumerate(zip(gpt_history, claude_history), 1):
        history_lines.append(f"Round {i} - Debater A (FOR):\n{g}")
        history_lines.append(f"Round {i} - Debater B (AGAINST):\n{c}")

    full_history = "\n\n".join(history_lines)

    messages = build_messages(
        JUDGE_PROMPT,
        f'Topic: "{topic}"\n\n{full_history}\n\nWho won this debate and why?'
    )

    return call_model_sync("claude", messages, session_id, round_num=4, metadata={"role": "judge"})
