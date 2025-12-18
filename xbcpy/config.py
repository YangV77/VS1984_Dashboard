# xbcpy/config.py
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class XbcConfig:
    token: str
    cmd_uds: str
    cli_uds: str


def _get_default_paths() -> tuple[str, str]:
    vs1984_cmd_uds = os.getenv("VS1984_CMD_UDS")
    xbcmd_push_uds = os.getenv("XBCMD_PUSH_UDS")
    if vs1984_cmd_uds and xbcmd_push_uds:
        return vs1984_cmd_uds, xbcmd_push_uds

    run = os.getenv("XDG_RUNTIME_DIR")
    if run:
        return f"{run}/vs1984/rsx_daemon.sock", f"{run}/vs1984/xmd_daemon.sock"

    return "/run/vs1984/rsx_daemon.sock", "/run/vs1984/xmd_daemon.sock"


def load_config() -> XbcConfig:
    token = os.getenv("DAEMONSVC_TOKEN") or "<user_set_DAEMONSVC_TOKEN>"
    if not token:
        raise RuntimeError("DAEMONSVC_TOKEN not set")

    cmd_default, push_default = _get_default_paths()
    cmd_uds = os.getenv("DAEMONSVC_UDS") or cmd_default
    cli_uds = os.getenv("DAEMONCLI_SOCK") or push_default

    return XbcConfig(token=token, cmd_uds=cmd_uds, cli_uds=cli_uds)
