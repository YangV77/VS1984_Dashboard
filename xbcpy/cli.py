# xbcpy/cli.py
import sys
import asyncio
from .client import XbcClient

async def _run(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: xbcpy <command...>")
        print('Example: xbcpy "cmd self"')
        return 2

    cmd = " ".join(argv[1:])

    cli = XbcClient.from_env()
    await cli.start()

    cli.on_log(lambda s: print(s, flush=True))

    status = await cli.send_cmd(cmd)
    if status != 200:
        print(f"[xbcpy] send_cmd failed: HTTP {status}", flush=True)
        await asyncio.sleep(0.5)
        await cli.stop()
        return 1

    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        await cli.stop()
        return 0

def main() -> None:
    raise SystemExit(asyncio.run(_run(sys.argv)))
