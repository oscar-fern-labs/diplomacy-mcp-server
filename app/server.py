from __future__ import annotations
import asyncio
from typing import Any, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from .jsonrpc import make_response, make_error, make_notification
from .db import get_pool
from .engine import initial_board_state, next_phase
import asyncpg
import secrets
import json

router = APIRouter()

connections: dict[str, set[WebSocket]] = {}

async def broadcast(game_code: str, payload: dict):
    conns = connections.get(game_code, set())
    dead: List[WebSocket] = []
    for ws in conns:
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            dead.append(ws)
    for ws in dead:
        conns.discard(ws)

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/games/{code}/board")
async def get_board(code: str):
    pool = await get_pool()
    game = await pool.fetchrow("SELECT * FROM games WHERE code=", code)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"game": dict(game)}

@router.get("/games/{code}/stream")
async def stream_board(code: str):
    from sse_starlette.sse import EventSourceResponse

    async def event_generator():
        pool = await get_pool()
        last_idx = -1
        while True:
            game = await pool.fetchrow("SELECT id, phase_index FROM games WHERE code=", code)
            if not game:
                yield {"event": "end", "data": "not found"}
                return
            if game["phase_index"] != last_idx:
                last_idx = game["phase_index"]
                phase = await pool.fetchrow(
                    "SELECT board_state, season, year, phase_type FROM phases WHERE game_id= AND index_in_game=",
                    game["id"], last_idx
                )
                if phase:
                    yield {"event": "board", "data": json.dumps({
                        "season": phase["season"],
                        "year": phase["year"],
                        "phase_type": phase["phase_type"],
                        "board_state": phase["board_state"],
                    })}
            await asyncio.sleep(2)
    return EventSourceResponse(event_generator())

@router.websocket("/mcp")
async def mcp_ws(ws: WebSocket):
    await ws.accept()
    game_code: Optional[str] = None
    player_id: Optional[str] = None
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
                mid = msg.get("id")
                method = msg.get("method")
                params = msg.get("params", {})

                if method == "initialize":
                    await ws.send_text(json.dumps(make_response({
                        "server": "diplomacy-mcp",
                        "version": "0.1.0",
                        "capabilities": [
                            "game.create", "game.join", "chat.send", "board.state", "order.submit", "ready.set"
                        ]
                    }, mid)))

                elif method == "game.create":
                    name = params.get("name") or "Diplomacy"
                    mapname = params.get("map") or "classic"
                    code = secrets.token_hex(3)
                    pool = await get_pool()
                    board = initial_board_state()
                    async with pool.acquire() as conn:
                        async with conn.transaction():
                            game_row = await conn.fetchrow(
                                "INSERT INTO games(code, name, map, phase_index, current_phase, status) VALUES(,,,,,) RETURNING *",
                                code, name, mapname, 0, board, "active"
                            )
                            await conn.execute(
                                "INSERT INTO phases(game_id, season, year, phase_type, index_in_game, board_state) VALUES(,,,,,)",
                                game_row["id"], board["season"], board["year"], board["phase_type"], 0, board
                            )
                    await ws.send_text(json.dumps(make_response({"code": code}, mid)))

                elif method == "game.join":
                    code = params["code"]
                    name = params["name"]
                    power = params.get("power")
                    pool = await get_pool()
                    game = await pool.fetchrow("SELECT * FROM games WHERE code=", code)
                    if not game:
                        await ws.send_text(json.dumps(make_error(-32000, "Game not found", mid)))
                        continue
                    token = secrets.token_hex(16)
                    try:
                        row = await pool.fetchrow(
                            "INSERT INTO players(game_id, name, power, token) VALUES(,,,) RETURNING id",
                            game["id"], name, power, token
                        )
                    except asyncpg.UniqueViolationError:
                        await ws.send_text(json.dumps(make_error(-32001, "Name or power already taken", mid)))
                        continue
                    game_code = code
                    player_id = str(row["id"])
                    connections.setdefault(game_code, set()).add(ws)
                    await broadcast(game_code, make_notification("event", {"type": "player_joined", "player": name}))
                    await ws.send_text(json.dumps(make_response({"token": token, "player_id": player_id}, mid)))

                elif method == "chat.send":
                    if not game_code:
                        await ws.send_text(json.dumps(make_error(-32010, "Join a game first", mid)))
                        continue
                    content = params["message"]
                    recipients = params.get("to", ["global"])
                    sender_name = params.get("from")
                    pool = await get_pool()
                    game = await pool.fetchrow("SELECT id FROM games WHERE code=", game_code)
                    await pool.execute(
                        "INSERT INTO messages(game_id, sender_player_id, recipients, content) VALUES(,,,)",
                        game["id"], player_id, recipients, content
                    )
                    await broadcast(game_code, make_notification("event", {"type": "chat_message", "from": sender_name, "to": recipients, "message": content}))
                    await ws.send_text(json.dumps(make_response({"ok": True}, mid)))

                elif method == "board.state":
                    code = params.get("code") or game_code
                    pool = await get_pool()
                    game = await pool.fetchrow("SELECT current_phase FROM games WHERE code=", code)
                    if not game:
                        await ws.send_text(json.dumps(make_error(-32000, "Game not found", mid)))
                        continue
                    await ws.send_text(json.dumps(make_response(game["current_phase"], mid)))

                elif method == "order.submit":
                    if not game_code:
                        await ws.send_text(json.dumps(make_error(-32010, "Join a game first", mid)))
                        continue
                    orders = params.get("orders", [])
                    pool = await get_pool()
                    async with pool.acquire() as conn:
                        async with conn.transaction():
                            g = await conn.fetchrow("SELECT id, current_phase, phase_index FROM games WHERE code=", game_code)
                            phase = await conn.fetchrow(
                                "SELECT id, orders FROM phases WHERE game_id= AND index_in_game=",
                                g["id"], g["phase_index"]
                            )
                            new_orders = list(phase["orders"]) if phase and phase["orders"] else []
                            new_orders.append({"player_id": player_id, "orders": orders})
                            await conn.execute("UPDATE phases SET orders= WHERE id=", new_orders, phase["id"])
                    await ws.send_text(json.dumps(make_response({"ok": True}, mid)))

                elif method == "ready.set":
                    if not game_code:
                        await ws.send_text(json.dumps(make_error(-32010, "Join a game first", mid)))
                        continue
                    ready = bool(params.get("ready", True))
                    pool = await get_pool()
                    async with pool.acquire() as conn:
                        async with conn.transaction():
                            g = await conn.fetchrow("SELECT id, phase_index FROM games WHERE code=", game_code)
                            await conn.execute("UPDATE players SET ready= WHERE id=", ready, player_id)
                            all_ready = await conn.fetchval("SELECT bool_and(ready) FROM players WHERE game_id=", g["id"])
                            if all_ready:
                                cur = await conn.fetchrow(
                                    "SELECT board_state, season, year, phase_type FROM phases WHERE game_id= AND index_in_game=",
                                    g["id"], g["phase_index"]
                                )
                                n_season, n_year, n_phase_type = next_phase(cur["season"], cur["year"], cur["phase_type"])
                                next_board = dict(cur["board_state"])  # TODO: adjudication
                                new_index = g["phase_index"] + 1
                                await conn.execute(
                                    "INSERT INTO phases(game_id, season, year, phase_type, index_in_game, board_state) VALUES(,,,,,)",
                                    g["id"], n_season, n_year, n_phase_type, new_index, next_board
                                )
                                await conn.execute(
                                    "UPDATE games SET phase_index=, current_phase= WHERE id=",
                                    new_index,
                                    {"season": n_season, "year": n_year, "phase_type": n_phase_type, "units": next_board.get("units", [])},
                                    g["id"]
                                )
                                await conn.execute("UPDATE players SET ready=false WHERE game_id=", g["id"])
                                await broadcast(game_code, make_notification("event", {"type": "phase_advanced", "season": n_season, "year": n_year, "phase_type": n_phase_type}))
                    await ws.send_text(json.dumps(make_response({"ok": True}, mid)))

                else:
                    await ws.send_text(json.dumps(make_error(-32601, "Method not found", mid)))

            except Exception as e:
                try:
                    await ws.send_text(json.dumps(make_error(-32099, str(e))))
                except Exception:
                    pass
    except WebSocketDisconnect:
        if game_code and ws in connections.get(game_code, set()):
            connections[game_code].discard(ws)
        return
