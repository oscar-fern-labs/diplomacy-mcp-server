import asyncio, json, os, sys, subprocess, time
import websockets

WS_URL = os.getenv("WS_URL", "ws://127.0.0.1:8080/mcp")
HTTP_BASE = os.getenv("HTTP_BASE", "http://127.0.0.1:8080")

async def recv_until_id(ws, target_id, max_msgs=20):
    notes = []
    for _ in range(max_msgs):
        raw = await ws.recv()
        try:
            obj = json.loads(raw)
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("id") == target_id:
            return obj, notes
        notes.append(obj)
    raise RuntimeError(f"Did not receive response id={target_id}; notes={notes}")

async def run_flow():
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize"}))
        r1, notes1 = await recv_until_id(ws, 1)
        print("INIT OK", r1)

        await ws.send(json.dumps({"jsonrpc":"2.0","id":2,"method":"game.create","params":{"name":"E2E Test"}}))
        r2, notes2 = await recv_until_id(ws, 2)
        print("CREATE OK", r2)
        code = r2["result"]["code"]
        open('/tmp/game_code.txt','w').write(code)

        await ws.send(json.dumps({"jsonrpc":"2.0","id":3,"method":"game.join","params":{"code":code,"name":"Tester","power":"England"}}))
        r3, _ = await recv_until_id(ws, 3)
        print("JOIN OK", r3)

        await ws.send(json.dumps({"jsonrpc":"2.0","id":4,"method":"chat.send","params":{"from":"Tester","message":"Hello MCP","to":["global"]}}))
        r4, notes4 = await recv_until_id(ws, 4)
        print("CHAT OK", r4)
        print("CHAT NOTES", notes4)

        await ws.send(json.dumps({"jsonrpc":"2.0","id":5,"method":"board.state","params":{}}))
        r5, _ = await recv_until_id(ws, 5)
        b1 = r5["result"]
        print("BOARD1", b1)
        assert b1.get("phase_type") in ("Movement", "Retreat", "Adjustment")

        # Start SSE stream in background
        ssecmd = ["bash","-lc", f"curl -sN {HTTP_BASE}/games/{code}/stream --max-time 8 > /tmp/sse_local.log 2>/dev/null & echo $!"]
        pid = subprocess.check_output(ssecmd, text=True).strip()
        time.sleep(1)

        await ws.send(json.dumps({"jsonrpc":"2.0","id":6,"method":"ready.set","params":{"ready":True}}))
        r6, notes6 = await recv_until_id(ws, 6)
        print("READY OK", r6)
        print("READY NOTES", notes6)
        await asyncio.sleep(3)

        await ws.send(json.dumps({"jsonrpc":"2.0","id":7,"method":"board.state","params":{}}))
        r7, _ = await recv_until_id(ws, 7)
        b2 = r7["result"]
        print("BOARD2", b2)
        return code, b1, b2

if __name__ == '__main__':
    code, b1, b2 = asyncio.get_event_loop().run_until_complete(run_flow())
    print("CODE:", code)
    print("PHASE1:", b1.get("phase_type"), b1.get("season"), b1.get("year"))
    print("PHASE2:", b2.get("phase_type"), b2.get("season"), b2.get("year"))

