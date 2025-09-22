from __future__ import annotations
from typing import Any, Dict

class JsonRpcError(Exception):
    def __init__(self, code: int, message: str, data: Any | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


def make_response(result: Any, id: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "result": result, "id": id}


def make_error(code: int, message: str, id: Any = None, data: Any | None = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": id}
    if data is not None:
        err["error"]["data"] = data
    return err


def make_notification(method: str, params: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "method": method, "params": params}
