import os

BASE_URL = "https://api.dialmycalls.com/2.0"


def get_auth() -> tuple[str, str]:
    return (os.getenv("DIALMYCALLS_API_KEY", ""), "")


def get_vanity_number_id() -> str:
    return os.getenv("DIALMYCALLS_VANITY_NUMBER_ID", "")
