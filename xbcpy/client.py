# xbcpy/client.py
import os
import json
import hmac
import asyncio
from typing import Callable, Optional, Set

import httpx
from aiohttp import web

from .config import XbcConfig, load_config
from .protocol import (
    CMD_ENDPOINT,
    PUSH_ENDPOINT,
    AUTH_HEADER,
    CONTENT_TYPE_JSON,
    FIELD_CMD,
    FIELD_XBC,
    MAX_JSON_BODY,
    DEFAULT_HTTP_TIMEOUT,
    DEFAULT_LOG_QUEUE_SIZE,
)


class XbcClient:
    """
    Mode B client:
      - send_cmd(): only delivers command to vs1984 (/xbc_command) over UDS
      - logs/results are pushed asynchronously to our UDS HTTP server (/xbc_response)

    Compatible with your existing xbcmd design:
      - Command channel:  HTTP POST JSON over UDS (curl --unix-socket)
      - Push channel:     vs1984 POST JSON back to our UDS server
    """

    def __init__(self, cfg: XbcConfig):
        self.cfg = cfg

        # httpx native UDS support (no extra dependency needed)
        self._transport = httpx.AsyncHTTPTransport(uds=self.cfg.cmd_uds)
        self._http = httpx.AsyncClient(transport=self._transport)

        # aiohttp UDS HTTP server for push channel
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.UnixSite] = None

        # subscribers
        self._subs: Set[asyncio.Queue[str]] = set()
        self._callbacks: Set[Callable[[str], None]] = set()
        self._lock = asyncio.Lock()

        self._started = False

    @staticmethod
    def from_env() -> "XbcClient":
        return XbcClient(load_config())

    async def start(self, max_body: int = MAX_JSON_BODY) -> None:
        """Start UDS HTTP server to receive /xbc_response push messages."""
        if self._started:
            return

        sock_path = self.cfg.cli_uds
        os.makedirs(os.path.dirname(sock_path), exist_ok=True)

        try:
            os.unlink(sock_path)
        except FileNotFoundError:
            pass

        async def handle_push(req: web.Request) -> web.Response:
            if req.path != PUSH_ENDPOINT:
                return web.json_response({"code": 0, "msg": "forbidden"}, status=403)

            if not hmac.compare_digest(req.headers.get(AUTH_HEADER, ""), self.cfg.token):
                return web.json_response({"code": 0, "msg": "unauthorized"}, status=401)

            ct = req.headers.get("Content-Type", "")
            if not ct.lower().startswith(CONTENT_TYPE_JSON):
                return web.json_response({"code": 0, "msg": "application/json only"}, status=415)

            raw = await req.read()
            if len(raw) > max_body:
                return web.json_response({"code": 0, "msg": "body too large"}, status=413)

            try:
                obj = json.loads(raw.decode("utf-8"))
                msg = obj.get(FIELD_XBC)
                if not isinstance(msg, str):
                    raise ValueError("missing xbc")
            except Exception:
                return web.json_response({"code": 0, "msg": "invalid json"}, status=400)

            await self._fanout(msg)

            return web.Response(status=200, text="\n")

        self._app = web.Application(client_max_size=max_body)
        self._app.router.add_post(PUSH_ENDPOINT, handle_push)

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()

        self._site = web.UnixSite(self._runner, sock_path)
        await self._site.start()

        try:
            os.chmod(sock_path, 0o660)
        except PermissionError:
            pass

        self._started = True

    async def stop(self) -> None:
        """Stop push server and close http client."""
        if self._site:
            await self._site.stop()
            self._site = None

        if self._runner:
            await self._runner.cleanup()
            self._runner = None

        self._app = None
        self._started = False

        await self._http.aclose()

        async with self._lock:
            self._subs.clear()
            self._callbacks.clear()

    async def send_cmd(self, cmd: str, timeout: float = DEFAULT_HTTP_TIMEOUT) -> int:
        """
        Deliver a command to vs1984 via HTTP over UDS.

        Equivalent to:
          curl --unix-socket $DAEMONSVC_UDS \
            -H "X-Auth-Token: $DAEMONSVC_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"cmd":"..."}' \
            http://localhost/xbc_command
        """
        try:
            r = await self._http.post(
                f"http://localhost{CMD_ENDPOINT}",
                headers={
                    AUTH_HEADER: self.cfg.token,
                    "Content-Type": CONTENT_TYPE_JSON,
                    "Accept": CONTENT_TYPE_JSON,
                },
                json={FIELD_CMD: cmd},
                timeout=timeout,
            )
            return r.status_code
        except Exception:
            return 0

    # ---------- subscription APIs ----------
    def on_log(self, cb: Callable[[str], None]) -> Callable[[], None]:
        self._callbacks.add(cb)

        def unsub() -> None:
            self._callbacks.discard(cb)

        return unsub

    def log_queue(self, maxsize: int = DEFAULT_LOG_QUEUE_SIZE) -> asyncio.Queue[str]:
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=maxsize)
        self._subs.add(q)
        return q

    async def subscribe(self, maxsize: int = DEFAULT_LOG_QUEUE_SIZE):

        q = self.log_queue(maxsize=maxsize)
        try:
            while True:
                yield await q.get()
        finally:
            self._subs.discard(q)

    # ---------- internal fanout ----------
    async def _fanout(self, msg: str) -> None:
        async with self._lock:
            for q in list(self._subs):
                try:
                    q.put_nowait(msg)
                except asyncio.QueueFull:
                    pass

            for cb in list(self._callbacks):
                try:
                    cb(msg)
                except Exception:
                    pass
