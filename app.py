"""
AI Debate Arena — FastAPI Application
Watch GPT-4o Mini and Claude Sonnet 4 debate any topic.
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
    MODELS,
    run_debate_round_streaming,
    judge_debate,
)

app = FastAPI(title="AI Debate Arena", version="1.0.0")
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
]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "preset_topics": PRESET_TOPICS,
        "models": MODELS,
    })


@app.post("/api/debate/start")
async def start_debate(request: Request):
    """Start a new debate session."""
    body = await request.json()
    topic = body.get("topic", "").strip()
    
    if not topic:
        return JSONResponse({"error": "Topic is required"}, status_code=400)
    
    session_id = str(uuid.uuid4())[:8]
    debates[session_id] = {
        "topic": topic,
        "session_id": session_id,
        "gpt_history": [],
        "claude_history": [],
        "current_round": 0,
        "total_rounds": 3,
        "status": "active",
    }
    
    return {"session_id": session_id, "topic": topic, "total_rounds": 3}


@app.get("/api/debate/{session_id}/round/{round_num}")
async def stream_round(session_id: str, round_num: int):
    """Stream a debate round via SSE."""
    debate = debates.get(session_id)
    if not debate:
        return JSONResponse({"error": "Debate not found"}, status_code=404)
    
    if round_num < 1 or round_num > debate["total_rounds"]:
        return JSONResponse({"error": "Invalid round number"}, status_code=400)
    
    def event_generator():
        for chunk in run_debate_round_streaming(
            topic=debate["topic"],
            round_num=round_num,
            session_id=session_id,
            gpt_history=debate["gpt_history"],
            claude_history=debate["claude_history"],
        ):
            event_type = chunk.get("type", "data")
            
            if event_type == "round_end":
                debate["gpt_history"].append(chunk["gpt_content"])
                debate["claude_history"].append(chunk["claude_content"])
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
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
