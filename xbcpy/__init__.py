# xbcpy/__init__.py
"""
xbcpy — Python SDK for controlling VS1984 (xbcmd-compatible)

- Command channel:  HTTP over Unix Domain Socket  -> POST /xbc_command
- Push channel:     Unix Domain Socket HTTP server -> POST /xbc_response
- Mode B: send_cmd() only delivers; logs/results are pushed asynchronously
"""

from .client import XbcClient
from .config import XbcConfig, load_config

__all__ = [
    "XbcClient",
    "XbcConfig",
    "load_config",
]

__version__ = "0.1.0"
