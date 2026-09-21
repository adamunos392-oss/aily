"""将 pycore success_response / error_response 映射为 api-contracts 扁平信封。"""

from typing import Any

from fastapi.responses import JSONResponse
from pycore.api import error_response, success_response


def success(data: Any, message: str = "ok") -> JSONResponse:
    """成功：HTTP 200，`{"code": 200, "message": "ok", "data": ...}`。"""
    wrapped = success_response(data=data, message=message)
    return JSONResponse(
        status_code=200,
        content={"code": 200, "message": wrapped.message or "ok", "data": wrapped.data},
    )


def failure(status_code: int, message: str, error_code: str) -> JSONResponse:
    """失败：HTTP 与 code 同为整数，data 为 null。"""
    _resp, _status = error_response(
        error=message, error_code=error_code, status_code=status_code
    )
    return JSONResponse(
        status_code=status_code,
        content={"code": status_code, "message": message, "data": None},
    )
