import os
import asyncio
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from xbcpy import XbcClient

ADMIN_TOKEN = os.getenv("XBCPY_ADMIN_TOKEN", "")

app = FastAPI(title="VS1984 Dashboard")

ws_clients: Set[WebSocket] = set()
ws_lock = asyncio.Lock()

xbc: XbcClient | None = None


def check_admin(token: str | None):
    if not ADMIN_TOKEN:
        return
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")


async def broadcast(msg: str):
    async with ws_lock:
        dead = []
        for ws in list(ws_clients):
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            ws_clients.discard(ws)


@app.on_event("startup")
async def on_startup():
    global xbc
    xbc = XbcClient.from_env()
    await xbc.start()

    xbc.on_log(lambda s: asyncio.create_task(broadcast(s)))


@app.on_event("shutdown")
async def on_shutdown():
    global xbc
    if xbc:
        await xbc.stop()
        xbc = None


INDEX_HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>VS1984 Dashboard</title>
  <style>
    body { font-family: system-ui; margin:0; }
    header { padding:12px 16px; border-bottom:1px solid #ddd; }
    main { padding:12px 16px; }
    #log { height: 70vh; overflow:auto; background:#0b0b0b; color:#eaeaea;
           padding:12px; border-radius:10px; white-space: pre-wrap; }
    .row { display:flex; gap:8px; margin-top:10px; }
    input { flex:1; padding:10px; border-radius:10px; border:1px solid #ccc; }
    button { padding:10px 14px; border-radius:10px; border:1px solid #ccc; cursor:pointer; }
    .hint { color:#666; font-size:12px; margin-top:8px; }
  </style>
</head>
<body>
<header><b>VS1984 Dashboard</b></header>
<main>
  <div id="log"></div>
  <div class="row">
    <input id="cmd" placeholder="cmd self" />
    <button onclick="sendCmd()">Send</button>
  </div>
  <div class="hint">URL 带 ?t=XBCPY_ADMIN_TOKEN。日志来自 /xbc_response 回推。</div>
</main>

<script>
  const logEl = document.getElementById("log");
  const cmdEl = document.getElementById("cmd");
  const t = new URLSearchParams(location.search).get("t") || "";

  function append(s){
    logEl.textContent += s + "\n";
    logEl.scrollTop = logEl.scrollHeight;
  }

  const wsProto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${wsProto}://${location.host}/ws?t=${encodeURIComponent(t)}`);
  ws.onopen = () => append("[ws] connected");
  ws.onclose = () => append("[ws] disconnected");
  ws.onerror = () => append("[ws] error");
  ws.onmessage = (e) => append(e.data);

  async function sendCmd(){
      const cmd = cmdEl.value.trim();
      if(!cmd) return;
      const r = await fetch(`/api/cmd?t=${encodeURIComponent(t)}`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({cmd})
      });
      const j = await r.json().catch(()=> ({}));
      append(`[send] ${cmd} -> HTTP ${r.status} ${JSON.stringify(j)}`);
      cmdEl.value = "";           // ✅ 发送后清空
      cmdEl.focus();              // ✅ 光标回到输入框
  }
  cmdEl.addEventListener("keydown", (e) => {
      // Enter = 发送
      // Shift + Enter = 保留（不发送）
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();   // 阻止默认行为（比如表单提交）
        sendCmd();
      }
  });
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    check_admin(ws.query_params.get("t"))
    await ws.accept()
    async with ws_lock:
        ws_clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        async with ws_lock:
            ws_clients.discard(ws)


@app.post("/api/cmd")
async def api_cmd(payload: dict, t: str | None = None):
    check_admin(t)

    cmd = (payload.get("cmd") or "").strip()
    if not cmd:
        return JSONResponse({"ok": 0, "msg": "missing cmd"}, status_code=400)

    if not xbc:
        return JSONResponse({"ok": 0, "msg": "xbc not ready"}, status_code=503)

    status = await xbc.send_cmd(cmd)
    return {"ok": 1 if status == 200 else 0, "http_status": status}
