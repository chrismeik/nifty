from abc import ABC, abstractmethod
from datetime import date


class SISAdapter(ABC):
    """
    Abstract base class for all SIS integrations.

    Each SIS (PowerSchool, Skyward, Infinite Campus, etc.) implements this
    interface. The pipeline works against this contract and never imports a
    specific SIS adapter directly.
    """

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def fetch(self, school_id: int, target_date: date) -> tuple[dict, dict]:
        """
        Pull attendance data for the given school and date.
        Returns (data, meta) where data has keys: students, attendance, contacts.
        """
        ...

    @abstractmethod
    async def stage(self, data: dict) -> dict:
        """
        Upsert raw SIS data into source-specific staging tables.
        Returns a metadata dict with row counts.
        """
        ...

    @abstractmethod
    async def transform(self, data: dict, target_date: date) -> dict:
        """
        Transform staged data into core.* Ed-Fi canonical tables.
        Returns a metadata dict with row counts.
        """
        ...
