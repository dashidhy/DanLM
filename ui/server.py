"""FastAPI server for GuanDan web game UI."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time

# Add project root to sys.path so we can import danzero
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
# Add ui/ to sys.path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from danzero.engine.actions import play_type_of

from ui_agent import UIAgent
from game_manager import GameSession, AI_THINK_DELAY

logger = logging.getLogger("guandan.server")

# Idle auto-shutdown: if no heartbeat received for this long, server exits.
IDLE_TIMEOUT = int(os.environ.get("GUANDAN_IDLE_TIMEOUT", "120"))  # seconds, 0=disabled
_last_heartbeat: float = time.monotonic()

app = FastAPI(title="GuanDan Game")


class NoCacheMiddleware(BaseHTTPMiddleware):
    """Disable browser caching for all responses during development."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

# Global state
sessions: dict[str, GameSession] = {}


def get_session(game_id: str) -> GameSession:
    if game_id not in sessions:
        raise HTTPException(status_code=404, detail="Game not found")
    return sessions[game_id]


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class NewGameRequest(BaseModel):
    mode: str = "single_round"  # "single_round" or "full_game"
    seed: int | None = None
    agent: str = "danzero_v1t"


class PlayRequest(BaseModel):
    game_id: str
    action_index: int


class GameIdRequest(BaseModel):
    game_id: str


class AutoPlayRequest(BaseModel):
    game_id: str
    enabled: bool


class HintToggleRequest(BaseModel):
    game_id: str
    enabled: bool


class ReorderRequest(BaseModel):
    game_id: str
    card_order: list[int]


class TributeActionRequest(BaseModel):
    game_id: str
    card_int: int


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@app.get("/api/heartbeat")
async def heartbeat():
    """Browser pings this periodically. Resets idle shutdown timer."""
    global _last_heartbeat
    _last_heartbeat = time.monotonic()
    return {"ok": True}


@app.get("/api/agents")
async def list_agents():
    """List available AI agents."""
    return UIAgent.list_agents()


@app.post("/api/new-game")
async def new_game(req: NewGameRequest):
    agent = UIAgent(req.agent)
    session = GameSession(agent=agent, mode=req.mode)
    sessions[session.game_id] = session

    if req.mode == "full_game":
        state = session.new_full_game()
    else:
        state = session.new_round(seed=req.seed)

    # Never auto-start AI turns — wait for user to click Continue on the
    # round-start overlay, which calls /api/confirm-tribute.
    return state


@app.get("/api/state")
async def get_state(game_id: str):
    session = get_session(game_id)
    return session.to_state_json()


@app.post("/api/play")
async def play_action(req: PlayRequest):
    session = get_session(req.game_id)

    if session.phase != "playing":
        raise HTTPException(status_code=400, detail="Game not in playing phase")

    obs = session.current_obs
    if obs is None or obs.player != session.human_seat:
        raise HTTPException(status_code=400, detail="Not your turn")

    if req.action_index < 0 or req.action_index >= obs.legal_plays.shape[0]:
        raise HTTPException(status_code=400, detail="Invalid action index")

    state = session.play_action(req.action_index)

    # After human plays, start AI turns
    if state["phase"] == "playing" and not state["is_human_turn"]:
        asyncio.create_task(_run_ai_turns(session))

    return state


@app.post("/api/pass")
async def pass_action(req: GameIdRequest):
    session = get_session(req.game_id)

    if session.phase != "playing" or session.current_obs is None:
        raise HTTPException(status_code=400, detail="Cannot pass now")

    # Find the pass action index
    obs = session.current_obs
    pass_idx = None
    for i in range(obs.legal_plays.shape[0]):
        if play_type_of(obs.legal_plays[i]) == "pass":
            pass_idx = i
            break

    if pass_idx is None:
        raise HTTPException(status_code=400, detail="Pass not available (you must play)")

    state = session.play_action(pass_idx)

    if state["phase"] == "playing" and not state["is_human_turn"]:
        asyncio.create_task(_run_ai_turns(session))

    return state


@app.post("/api/hint")
async def toggle_hint(req: HintToggleRequest):
    session = get_session(req.game_id)
    session.hint_enabled = req.enabled
    return session.to_state_json()


@app.post("/api/auto-play")
async def toggle_auto_play(req: AutoPlayRequest):
    session = get_session(req.game_id)
    session.auto_play = req.enabled

    state = session.to_state_json()

    # If enabling auto-play and it's currently human's turn (or any turn), start AI
    if req.enabled and state["phase"] == "playing":
        asyncio.create_task(_run_ai_turns(session))

    return state


@app.post("/api/tribute-action")
async def tribute_action(req: TributeActionRequest):
    session = get_session(req.game_id)

    if session.phase not in ("tribute_give", "tribute_back"):
        raise HTTPException(status_code=400, detail="Not in tribute phase")

    state = session.tribute_action(req.card_int)

    # After tribute completes, do NOT auto-start AI — wait for /api/confirm-tribute
    return state


@app.post("/api/tribute-auto")
async def tribute_auto(req: GameIdRequest):
    """AI auto-selects tribute card for human seat."""
    session = get_session(req.game_id)
    if session.phase not in ("tribute_give", "tribute_back"):
        raise HTTPException(status_code=400, detail="Not in tribute phase")
    state = session.auto_tribute()
    return state


@app.post("/api/confirm-tribute")
async def confirm_tribute(req: GameIdRequest):
    """User confirms they've seen the tribute info. Now start AI turns."""
    session = get_session(req.game_id)
    state = session.to_state_json()

    if state["phase"] == "playing" and not state["is_human_turn"]:
        asyncio.create_task(_run_ai_turns(session))

    return state


@app.post("/api/continue-tribute")
async def continue_tribute(req: GameIdRequest):
    """User has reviewed give results. Continue to back phase."""
    session = get_session(req.game_id)

    if session.phase != "tribute_give_done":
        raise HTTPException(status_code=400, detail="Not in tribute_give_done phase")

    state = session.continue_tribute()
    return state


@app.post("/api/reorder-hand")
async def reorder_hand(req: ReorderRequest):
    session = get_session(req.game_id)
    session.hand_order = req.card_order
    return {"ok": True}


@app.post("/api/next-round")
async def next_round(req: GameIdRequest):
    session = get_session(req.game_id)

    if session.mode != "full_game":
        raise HTTPException(status_code=400, detail="Not a full game")

    state = session.next_round()
    return state


@app.post("/api/new-round")
async def new_round(req: GameIdRequest):
    """Start a new single round (for single_round mode replay)."""
    session = get_session(req.game_id)
    state = session.new_round()
    return state


# ---------------------------------------------------------------------------
# AI turn runner (async with delay)
# ---------------------------------------------------------------------------

async def _run_ai_turns(session: GameSession) -> None:
    """Run AI turns with delay, until it's human's turn or round ends."""
    try:
        while session.phase == "playing":
            obs = session.current_obs
            if obs is None:
                break

            # If it's human's turn and auto-play is off, stop
            if obs.player == session.human_seat and not session.auto_play:
                break

            # Wait for AI "thinking" time
            await asyncio.sleep(AI_THINK_DELAY)

            # Advance one AI turn
            result = session.advance_one_ai()
            if result is None:
                break
    except Exception:
        logger.exception("AI turn crashed")


# ---------------------------------------------------------------------------
# Idle auto-shutdown watchdog
# ---------------------------------------------------------------------------

async def _idle_watchdog() -> None:
    """Background task: exit if no heartbeat received within IDLE_TIMEOUT."""
    while True:
        await asyncio.sleep(30)  # check every 30s
        idle = time.monotonic() - _last_heartbeat
        if idle > IDLE_TIMEOUT:
            logger.info("No heartbeat for %.0fs (timeout=%ds), shutting down.", idle, IDLE_TIMEOUT)
            os._exit(0)


@app.on_event("startup")
async def _start_watchdog():
    global _last_heartbeat
    _last_heartbeat = time.monotonic()
    if IDLE_TIMEOUT > 0:
        asyncio.create_task(_idle_watchdog())
        logger.info("Idle watchdog started (timeout=%ds)", IDLE_TIMEOUT)


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

# Mount static files (must be after API routes)
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@app.get("/")
async def index():
    return FileResponse(os.path.join(static_dir, "index.html"))


app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
