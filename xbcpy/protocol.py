# xbcpy/protocol.py

CMD_ENDPOINT = "/xbc_command"
PUSH_ENDPOINT = "/xbc_response"

AUTH_HEADER = "X-Auth-Token"
CONTENT_TYPE_JSON = "application/json"

FIELD_CMD = "cmd"
FIELD_XBC = "xbc"

MAX_JSON_BODY = 64 * 1024
DEFAULT_HTTP_TIMEOUT = 20.0
DEFAULT_LOG_QUEUE_SIZE = 1024

PROTOCOL_VERSION = 1
