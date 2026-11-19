# app/observability.py
import logging
import os
import time
from typing import Callable, Awaitable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pythonjsonlogger import jsonlogger

# Optional service label for easier Grafana filtering (e.g., "api", "worker")
SERVICE = os.getenv("SERVICE_NAME", "").strip() or "app"

# ---- Prometheus metrics (namespaced) ----
REQUESTS_TOTAL = Counter(
    "app_http_requests",
    "Total HTTP requests",
    labelnames=("service", "route", "method", "status"),
)

REQUEST_DURATION = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request duration (seconds)",
    labelnames=("service", "route", "method"),
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)


def setup_json_logging(level: int = logging.INFO) -> None:
    """Configure stdlib logging to emit JSON lines."""
    root = logging.getLogger()
    # Avoid duplicate handlers if re-called in tests
    root.handlers.clear()

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level)

    # Prevent logs from propagating to other (e.g., uvicorn) handlers twice
    root.propagate = False


def route_template_from_request(request: Request) -> str:
    route = request.scope.get("route")
    if route and getattr(route, "path", None):
        return route.path
    return request.url.path


async def metrics_endpoint() -> Response:
    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


async def timing_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.perf_counter()
    route = route_template_from_request(request)
    method = request.method
    status = "500"

    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    finally:
        duration = time.perf_counter() - start
        REQUEST_DURATION.labels(service=SERVICE, route=route, method=method).observe(duration)
        REQUESTS_TOTAL.labels(service=SERVICE, route=route, method=method, status=status).inc()

        request_id = (
            request.headers.get("x-request-id")
            or request.headers.get("X-Request-Id")
            or ""
        )

        logging.getLogger("http").info(
            "request",
            extra={
                "route": route,
                "method": method,
                "status": status,
                "duration_ms": round(duration * 1000, 2),
                "request_id": request_id,
            },
        )
