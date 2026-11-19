# app/logging_json.py
from logging.config import dictConfig
from pythonjsonlogger import jsonlogger

class UvicornJSONFormatter(jsonlogger.JsonFormatter):
    """Adds common fields + handles uvicorn.access extras cleanly."""
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        # Standard fields
        log_record.setdefault("level", record.levelname)
        log_record.setdefault("logger", record.name)
        log_record.setdefault("pathname", record.pathname)
        log_record.setdefault("lineno", record.lineno)

        # If it's an access log, uvicorn puts useful extras on the record
        if record.name == "uvicorn.access":
            for key in ("client_addr", "request_line", "status_code", "http_version", "method", "path"):
                if hasattr(record, key):
                    log_record[key] = getattr(record, key)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": UvicornJSONFormatter,
            # Put whatever keys you like here; jsonlogger accepts a format string too.
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "loggers": {
        # Your app
        "app": {"handlers": ["console"], "level": "INFO", "propagate": False},
        # FastAPI / uvicorn
        "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["console"], "level": "INFO", "propagate": False},
        # Starlette / FastAPI internals if you want them
        "fastapi": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "starlette": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "asyncio": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

def configure_logging():
    dictConfig(LOGGING_CONFIG)
