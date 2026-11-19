from _app._dramatiq.settings import DramatiqSettings
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend

# Optional Prometheus middleware
_PROM_AVAILABLE = False
try:
    from dramatiq.middleware.prometheus import Prometheus
    _PROM_AVAILABLE = True
except Exception:
    pass

# Configure broker/results on the broker Redis
_broker_url = DramatiqSettings().redis_broker_url
redis_broker = RedisBroker(url=_broker_url)
dramatiq.set_broker(redis_broker)

results_backend = RedisBackend(url=_broker_url)
redis_broker.add_middleware(Results(backend=results_backend))

# Only add Prometheus if available AND not already present
if _PROM_AVAILABLE and not any(m.__class__.__name__ == "Prometheus" for m in redis_broker.middleware):
    redis_broker.add_middleware(Prometheus())

# Do NOT add AgeLimit/TimeLimit/Retries here; the Dramatiq CLI injects them already.
# This avoids the “same middleware twice” warnings.
