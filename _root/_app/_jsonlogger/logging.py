import contextvars
import json
import logging
import sys
from typing import Any, Dict, Optional

_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)

SENSITIVE_KEYS = {"authorization", "cookie", "set-cookie", "x-api-key", "password", "token", "secret", "redis_password"}

def set_request_id(value: Optional[str]) -> None:
    _request_id_var.set(value)

def get_request_id() -> Optional[str]:
    return _request_id_var.get()

def _sanitize(obj: Any) -> Any:
    try:
        if isinstance(obj, dict):
            clean: Dict[str, Any] = {}
            for k, v in obj.items():
                if isinstance(k, str) and k.lower() in SENSITIVE_KEYS:
                    clean[k] = "***redacted***"
                else:
                    clean[k] = _sanitize(v)
            return clean
        elif isinstance(obj, list):
            return [_sanitize(x) for x in obj]
        elif isinstance(obj, str):
            return (obj[:2048] + "...(truncated)") if len(obj) > 2048 else obj
        else:
            return obj
    except Exception:
        return obj

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            rid = _request_id_var.get()
        except LookupError:
            rid = None
        setattr(record, "request_id", rid)
        return True

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("request_id", "message_id", "payload", "headers"):
            if hasattr(record, key):
                base[key] = getattr(record, key)
        base = _sanitize(base)
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)

def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.addFilter(RequestIdFilter())
    root.setLevel(level.upper())
