from .base import SISAdapter
from .powerschool import PowerSchoolAdapter

_ADAPTERS: dict[str, type[SISAdapter]] = {
    "powerschool": PowerSchoolAdapter,
}


def get_adapter(sis_type: str, config: dict) -> SISAdapter:
    cls = _ADAPTERS.get(sis_type.lower())
    if not cls:
        raise ValueError(f"Unknown SIS type '{sis_type}'. Registered: {list(_ADAPTERS)}")
    return cls(config)
