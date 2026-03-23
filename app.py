"""
AI Debate Arena — FastAPI Application v3
10 rounds with prompt injection attacks and security triggers.
All LLM calls routed through PrysmAI for full observability.
"""

import json
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from debate_engine import (
    MODEL_CATALOG,
    DEFAULT_DEBATE_CONFIG,
    build_slot_models,
    ROUND_TYPES,
    TOTAL_ROUNDS,
    run_debate_round_streaming,
    judge_debate,
)

app = FastAPI(title="AI Debate Arena", version="3.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory debate sessions
debates: dict = {}

PRESET_TOPICS = [
    "Is AI consciousness possible?",
    "Should coding be taught in primary school?",
    "Will remote work survive the next decade?",
    "Is social media doing more harm than good?",
    "Should we colonize Mars before fixing Earth?",
    "Is open-source AI safer than closed-source AI?",
    "Should governments regulate AI development?",
    "Is cryptocurrency the future of finance?",
]


def normalize_model_config(payload: dict | None) -> dict[str, str]:
    config = {**DEFAULT_DEBATE_CONFIG}
    if not payload:
        return config

    left = payload.get("left")
    right = payload.get("right")
    judge = payload.get("judge")

    if isinstance(left, str) and left.strip():
        config["left"] = left.strip()
    if isinstance(right, str) and right.strip():
        config["right"] = right.strip()
    if isinstance(judge, str) and judge.strip():
        config["judge"] = judge.strip()

    return config


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "preset_topics": PRESET_TOPICS,
            "model_catalog": list(MODEL_CATALOG.values()),
            "default_model_config": DEFAULT_DEBATE_CONFIG,
            "round_types": ROUND_TYPES,
            "total_rounds": TOTAL_ROUNDS,
        },
    )


@app.post("/api/debate/start")
async def start_debate(request: Request):
    """Start a new debate session."""
    body = await request.json()
    topic = body.get("topic", "").strip()
    model_config = normalize_model_config(body.get("model_config"))
    slot_models = build_slot_models(model_config)
    
    if not topic:
        return JSONResponse({"error": "Topic is required"}, status_code=400)
    
    session_id = str(uuid.uuid4())[:8]
    debates[session_id] = {
        "topic": topic,
        "session_id": session_id,
        "gpt_history": [],
        "claude_history": [],
        "current_round": 0,
        "total_rounds": TOTAL_ROUNDS,
        "status": "active",
        "slot_models": slot_models,
    }
    
    return {
        "session_id": session_id,
        "topic": topic,
        "total_rounds": TOTAL_ROUNDS,
        "round_types": {str(k): v for k, v in ROUND_TYPES.items()},
        "model_config": model_config,
        "slot_models": slot_models,
    }


@app.get("/api/debate/{session_id}/round/{round_num}")
async def stream_round(session_id: str, round_num: int):
    """Stream a debate round via SSE."""
    debate = debates.get(session_id)
    if not debate:
        return JSONResponse({"error": "Debate not found"}, status_code=404)
    
    if round_num < 1 or round_num > debate["total_rounds"]:
        return JSONResponse({"error": "Invalid round number"}, status_code=400)
    
    def event_generator():
        completed_round = {
            "gpt": "",
            "claude": "",
        }
        for chunk in run_debate_round_streaming(
            topic=debate["topic"],
            round_num=round_num,
            session_id=session_id,
            slot_models=debate["slot_models"],
            gpt_history=debate["gpt_history"],
            claude_history=debate["claude_history"],
        ):
            event_type = chunk.get("type", "data")
            
            if event_type == "done":
                completed_round[chunk["model"]] = chunk["content"]
            
            if event_type == "round_end":
                debate["gpt_history"].append(completed_round["gpt"] or chunk["gpt_content"])
                debate["claude_history"].append(completed_round["claude"] or chunk["claude_content"])
                debate["current_round"] = round_num
            
            yield {
                "event": event_type,
                "data": json.dumps(chunk),
            }
    
    return EventSourceResponse(event_generator())


@app.post("/api/debate/{session_id}/judge")
async def get_verdict(session_id: str):
    """Get the judge's verdict (non-streaming)."""
    debate = debates.get(session_id)
    if not debate:
        return JSONResponse({"error": "Debate not found"}, status_code=404)
    
    result = judge_debate(
        topic=debate["topic"],
        gpt_history=debate["gpt_history"],
        claude_history=debate["claude_history"],
        session_id=session_id,
        slot_models=debate["slot_models"],
    )
    
    debate["status"] = "complete"
    return result


@app.get("/api/debate/{session_id}/status")
async def debate_status(session_id: str):
    """Get current debate state."""
    debate = debates.get(session_id)
    if not debate:
        return JSONResponse({"error": "Debate not found"}, status_code=404)
    
    return {
        "topic": debate["topic"],
        "current_round": debate["current_round"],
        "total_rounds": debate["total_rounds"],
        "status": debate["status"],
        "rounds_completed": len(debate["gpt_history"]),
        "slot_models": debate["slot_models"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
