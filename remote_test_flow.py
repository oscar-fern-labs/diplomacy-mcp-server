import asyncio, json, os, ssl, subprocess, time
import websockets

BASE = "https://diplomacy-mcp-backend-morphvm-hlfn7cve.http.cloud.morph.so"
WS = BASE.replace("https://","wss://") + "/mcp"

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
    sslctx = ssl.create_default_context()
    async with websockets.connect(WS, ssl=sslctx) as ws:
        await ws.send(json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize"}))
        r1, _ = await recv_until_id(ws, 1)
        await ws.send(json.dumps({"jsonrpc":"2.0","id":2,"method":"game.create","params":{"name":"Remote E2E"}}))
        r2, _ = await recv_until_id(ws, 2)
        code = r2["result"]["code"]
        open("/tmp/remote_game_code.txt","w").write(code)
        await ws.send(json.dumps({"jsonrpc":"2.0","id":3,"method":"game.join","params":{"code":code,"name":"RemoteTester","power":"England"}}))
        _r3, _ = await recv_until_id(ws, 3)
        ssecmd = ["bash","-lc", f"curl -sN {BASE}/games/{code}/stream --max-time 10 > /tmp/sse_remote.log 2>/dev/null & echo $!"]
        _pid = subprocess.check_output(ssecmd, text=True).strip()
        time.sleep(1)
        await ws.send(json.dumps({"jsonrpc":"2.0","id":4,"method":"ready.set","params":{"ready":True}}))
        _r4, _ = await recv_until_id(ws, 4)
        await asyncio.sleep(3)
        await ws.send(json.dumps({"jsonrpc":"2.0","id":5,"method":"board.state","params":{"code":code}}))
        r5, _ = await recv_until_id(ws, 5)
        return code, r5["result"]

code, board = asyncio.get_event_loop().run_until_complete(run_flow())
print("REMOTE_CODE:", code)
print("REMOTE_PHASE:", board.get("phase_type"), board.get("season"), board.get("year"))
