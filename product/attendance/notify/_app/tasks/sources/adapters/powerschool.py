# <product id="e3c58415-5a7b-4c41-afd2-d75b900dbbdc">
from datetime import date

from attendance.powerschool._app.pull import fetch_powerschool_data
from attendance.powerschool._app.stage import stage_to_postgres
from attendance.powerschool._app.transform import transform_to_core

from .base import SISAdapter


class PowerSchoolAdapter(SISAdapter):

    def fetch(self, school_id: int, target_date: date) -> tuple[dict, dict]:
        return fetch_powerschool_data(school_id, target_date)

    async def stage(self, data: dict) -> dict:
        return await stage_to_postgres(data)

    async def transform(self, data: dict, target_date: date) -> dict:
        return await transform_to_core(data, target_date)
# </product>
