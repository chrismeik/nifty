# app/job_metrics.py
import os
import time
from typing import Optional

from prometheus_client import Counter, Histogram, Gauge, start_http_server


# -------- Rate limit (used by deps.py) --------
RATE_LIMIT_HITS_TOTAL = Counter(
    "app_rate_limit_hits", "Requests evaluated by the rate limiter"
)
RATE_LIMIT_BLOCKED_TOTAL = Counter(
    "app_rate_limit_blocked", "Requests blocked by the rate limiter"
)

# -------- DLQ / requeue (used by API + worker) --------
INGEST_DLQ_TOTAL = Counter(
    "app_ingest_dlq", "Total messages sent to dead-letter queue"
)
INGEST_REQUEUES_TOTAL = Counter(
    "app_ingest_requeues", "Total messages requeued from dead-letter queue"
)

# -------- Worker throughput + latency --------
JOBS_PROCESSED_TOTAL = Counter(
    "app_jobs_processed",
    "Jobs processed (by outcome)",
    labelnames=("task", "outcome"),  # outcome ∈ {success, fail}
)
JOB_DURATION_SECONDS = Histogram(
    "app_job_duration_seconds",
    "Job runtime (seconds)",
    labelnames=("task",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5, 10, 30),
)
JOBS_IN_PROGRESS = Gauge(
    "app_jobs_in_progress", "Number of jobs currently processing", ["task"]
)


def time_job(task_name: str):
    """Context manager to measure runtime and record success/fail for a job."""
    class _Timer:
        def __enter__(self):
            self._t0 = time.perf_counter()
            try:
                JOBS_IN_PROGRESS.labels(task=task_name).inc()
            except Exception:
                pass
            return self

        def __exit__(self, exc_type, exc, tb):
            dur = time.perf_counter() - self._t0
            try:
                JOB_DURATION_SECONDS.labels(task=task_name).observe(dur)
            finally:
                try:
                    JOBS_IN_PROGRESS.labels(task=task_name).dec()
                except Exception:
                    pass
            outcome = "fail" if exc_type else "success"
            JOBS_PROCESSED_TOTAL.labels(task=task_name, outcome=outcome).inc()
            return False  # don't suppress exceptions

    return _Timer()


def start_worker_metrics_server(port: Optional[int] = None) -> None:
    """Expose Prometheus /metrics for the worker process."""
    if port is None:
        port = int(os.getenv("WORKER_METRICS_PORT", "8001"))
    start_http_server(port)
