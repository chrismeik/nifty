"""
Step 1 — Pull attendance data from PowerSchool.

Idempotency: if today's parquet files already exist on disk, the API call is
skipped and data is loaded from disk instead. Re-running the pipeline on the
same day is always safe.

The spoofed implementation uses the date as a random seed so each day produces
a consistent but unique set of 2–6 absent students. Replace _call_powerschool_api
with a real HTTP client when credentials are available.
"""

import random
import logging
from datetime import date
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

# Hive layout: <schema>/<table>/year=YYYY/month=MM/day=DD/school_id=NNN/<table>.parquet
_DATA_DIR = Path("/root-product/product/attendance/powerschool/_data/_postgres/nifty/powerschool")

# ---------------------------------------------------------------------------
# Fixed student pool (20 students, 2 schools)
# ---------------------------------------------------------------------------
_STUDENTS = [
    {"ps_student_id": 1001, "student_number": "S001", "first_name": "Emma",    "last_name": "Johnson",   "grade_level": 9,  "school_id": 101},
    {"ps_student_id": 1002, "student_number": "S002", "first_name": "Liam",    "last_name": "Williams",  "grade_level": 10, "school_id": 101},
    {"ps_student_id": 1003, "student_number": "S003", "first_name": "Olivia",  "last_name": "Brown",     "grade_level": 11, "school_id": 101},
    {"ps_student_id": 1004, "student_number": "S004", "first_name": "Noah",    "last_name": "Jones",     "grade_level": 12, "school_id": 101},
    {"ps_student_id": 1005, "student_number": "S005", "first_name": "Ava",     "last_name": "Garcia",    "grade_level": 9,  "school_id": 101},
    {"ps_student_id": 1006, "student_number": "S006", "first_name": "Elijah",  "last_name": "Miller",    "grade_level": 10, "school_id": 101},
    {"ps_student_id": 1007, "student_number": "S007", "first_name": "Sophia",  "last_name": "Davis",     "grade_level": 11, "school_id": 101},
    {"ps_student_id": 1008, "student_number": "S008", "first_name": "James",   "last_name": "Martinez",  "grade_level": 12, "school_id": 101},
    {"ps_student_id": 1009, "student_number": "S009", "first_name": "Isabella","last_name": "Hernandez", "grade_level": 9,  "school_id": 101},
    {"ps_student_id": 1010, "student_number": "S010", "first_name": "Logan",   "last_name": "Lopez",     "grade_level": 10, "school_id": 101},
    {"ps_student_id": 1011, "student_number": "S011", "first_name": "Mia",     "last_name": "Gonzalez",  "grade_level": 9,  "school_id": 102},
    {"ps_student_id": 1012, "student_number": "S012", "first_name": "Lucas",   "last_name": "Wilson",    "grade_level": 10, "school_id": 102},
    {"ps_student_id": 1013, "student_number": "S013", "first_name": "Amelia",  "last_name": "Anderson",  "grade_level": 11, "school_id": 102},
    {"ps_student_id": 1014, "student_number": "S014", "first_name": "Mason",   "last_name": "Thomas",    "grade_level": 12, "school_id": 102},
    {"ps_student_id": 1015, "student_number": "S015", "first_name": "Harper",  "last_name": "Taylor",    "grade_level": 9,  "school_id": 102},
    {"ps_student_id": 1016, "student_number": "S016", "first_name": "Ethan",   "last_name": "Moore",     "grade_level": 10, "school_id": 102},
    {"ps_student_id": 1017, "student_number": "S017", "first_name": "Evelyn",  "last_name": "Jackson",   "grade_level": 11, "school_id": 102},
    {"ps_student_id": 1018, "student_number": "S018", "first_name": "Aiden",   "last_name": "Martin",    "grade_level": 12, "school_id": 102},
    {"ps_student_id": 1019, "student_number": "S019", "first_name": "Abigail", "last_name": "Lee",       "grade_level": 9,  "school_id": 102},
    {"ps_student_id": 1020, "student_number": "S020", "first_name": "Carter",  "last_name": "Perez",     "grade_level": 10, "school_id": 102},
]

# One primary contact per student
_CONTACTS = {
    1001: {"ps_contact_id": 5001, "ps_student_id": 1001, "first_name": "Sarah",    "last_name": "Johnson",   "relationship": "Mother", "priority_order": 1, "phone": "555-0101", "email": "sarah.johnson@email.com"},
    1002: {"ps_contact_id": 5002, "ps_student_id": 1002, "first_name": "David",    "last_name": "Williams",  "relationship": "Father", "priority_order": 1, "phone": "555-0102", "email": "david.williams@email.com"},
    1003: {"ps_contact_id": 5003, "ps_student_id": 1003, "first_name": "Karen",    "last_name": "Brown",     "relationship": "Mother", "priority_order": 1, "phone": "555-0103", "email": "karen.brown@email.com"},
    1004: {"ps_contact_id": 5004, "ps_student_id": 1004, "first_name": "Michael",  "last_name": "Jones",     "relationship": "Father", "priority_order": 1, "phone": "555-0104", "email": "michael.jones@email.com"},
    1005: {"ps_contact_id": 5005, "ps_student_id": 1005, "first_name": "Lisa",     "last_name": "Garcia",    "relationship": "Mother", "priority_order": 1, "phone": "555-0105", "email": "lisa.garcia@email.com"},
    1006: {"ps_contact_id": 5006, "ps_student_id": 1006, "first_name": "Robert",   "last_name": "Miller",    "relationship": "Father", "priority_order": 1, "phone": "555-0106", "email": "robert.miller@email.com"},
    1007: {"ps_contact_id": 5007, "ps_student_id": 1007, "first_name": "Nancy",    "last_name": "Davis",     "relationship": "Mother", "priority_order": 1, "phone": "555-0107", "email": "nancy.davis@email.com"},
    1008: {"ps_contact_id": 5008, "ps_student_id": 1008, "first_name": "Thomas",   "last_name": "Martinez",  "relationship": "Father", "priority_order": 1, "phone": "555-0108", "email": "thomas.martinez@email.com"},
    1009: {"ps_contact_id": 5009, "ps_student_id": 1009, "first_name": "Betty",    "last_name": "Hernandez", "relationship": "Mother", "priority_order": 1, "phone": "555-0109", "email": "betty.hernandez@email.com"},
    1010: {"ps_contact_id": 5010, "ps_student_id": 1010, "first_name": "Charles",  "last_name": "Lopez",     "relationship": "Father", "priority_order": 1, "phone": "555-0110", "email": "charles.lopez@email.com"},
    1011: {"ps_contact_id": 5011, "ps_student_id": 1011, "first_name": "Sandra",   "last_name": "Gonzalez",  "relationship": "Mother", "priority_order": 1, "phone": "555-0111", "email": "sandra.gonzalez@email.com"},
    1012: {"ps_contact_id": 5012, "ps_student_id": 1012, "first_name": "Mark",     "last_name": "Wilson",    "relationship": "Father", "priority_order": 1, "phone": "555-0112", "email": "mark.wilson@email.com"},
    1013: {"ps_contact_id": 5013, "ps_student_id": 1013, "first_name": "Donna",    "last_name": "Anderson",  "relationship": "Mother", "priority_order": 1, "phone": "555-0113", "email": "donna.anderson@email.com"},
    1014: {"ps_contact_id": 5014, "ps_student_id": 1014, "first_name": "Paul",     "last_name": "Thomas",    "relationship": "Father", "priority_order": 1, "phone": "555-0114", "email": "paul.thomas@email.com"},
    1015: {"ps_contact_id": 5015, "ps_student_id": 1015, "first_name": "Carol",    "last_name": "Taylor",    "relationship": "Mother", "priority_order": 1, "phone": "555-0115", "email": "carol.taylor@email.com"},
    1016: {"ps_contact_id": 5016, "ps_student_id": 1016, "first_name": "Steven",   "last_name": "Moore",     "relationship": "Father", "priority_order": 1, "phone": "555-0116", "email": "steven.moore@email.com"},
    1017: {"ps_contact_id": 5017, "ps_student_id": 1017, "first_name": "Ruth",     "last_name": "Jackson",   "relationship": "Mother", "priority_order": 1, "phone": "555-0117", "email": "ruth.jackson@email.com"},
    1018: {"ps_contact_id": 5018, "ps_student_id": 1018, "first_name": "Kenneth",  "last_name": "Martin",    "relationship": "Father", "priority_order": 1, "phone": "555-0118", "email": "kenneth.martin@email.com"},
    1019: {"ps_contact_id": 5019, "ps_student_id": 1019, "first_name": "Sharon",   "last_name": "Lee",       "relationship": "Mother", "priority_order": 1, "phone": "555-0119", "email": "sharon.lee@email.com"},
    1020: {"ps_contact_id": 5020, "ps_student_id": 1020, "first_name": "Edward",   "last_name": "Perez",     "relationship": "Father", "priority_order": 1, "phone": "555-0120", "email": "edward.perez@email.com"},
}


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def fetch_powerschool_data(school_id: int, target_date: date) -> tuple[dict, dict]:
    """
    Returns (data, meta) for a specific school and date.

    Checks for existing parquet files first. If found, loads from disk and
    returns source='cache'. If not found, calls (spoofed) API, writes parquet
    files, and returns source='api'.
    """
    if _parquet_path("attendance", school_id, target_date).exists():
        log.info("step1: parquet already exists for school=%s %s — loading from disk", school_id, target_date)
        data = _load_from_parquet(school_id, target_date)
        meta = {
            "source":         "cache",
            "school_id":      school_id,
            "students_count": len(data["students"]),
            "absence_count":  len(data["attendance"]),
            "contact_count":  len(data["contacts"]),
        }
        return data, meta

    log.info("step1: pulling PowerSchool data for school=%s %s", school_id, target_date)
    data = _call_powerschool_api(school_id, target_date)

    _write_parquet("students",   data["students"],   school_id, target_date)
    _write_parquet("attendance", data["attendance"], school_id, target_date)
    _write_parquet("contacts",   data["contacts"],   school_id, target_date)

    meta = {
        "source":         "api",
        "school_id":      school_id,
        "students_count": len(data["students"]),
        "absence_count":  len(data["attendance"]),
        "contact_count":  len(data["contacts"]),
    }
    log.info("step1: wrote parquet — %d absent students, %d contacts", meta["absence_count"], meta["contact_count"])
    return data, meta


# ---------------------------------------------------------------------------
# Spoofed API — replace with real HTTP client when credentials are available
# ---------------------------------------------------------------------------

def _call_powerschool_api(school_id: int, target_date: date) -> dict:
    school_students = [s for s in _STUDENTS if s["school_id"] == school_id]
    rng = random.Random(f"{school_id}-{target_date.isoformat()}")
    absent_count = rng.randint(2, min(6, len(school_students)))
    absent_students = rng.sample(school_students, absent_count)

    attendance = [
        {
            "ps_attendance_id": rng.randint(100_000, 999_999),
            "ps_student_id":    s["ps_student_id"],
            "school_id":        s["school_id"],
            "att_date":         target_date.isoformat(),
            "att_code":         "UA",
            "description":      "Unexcused Absence",
        }
        for s in absent_students
    ]

    contacts = [_CONTACTS[s["ps_student_id"]] for s in absent_students]

    return {"students": absent_students, "attendance": attendance, "contacts": contacts}


# ---------------------------------------------------------------------------
# Parquet helpers
# ---------------------------------------------------------------------------

def _parquet_path(table: str, school_id: int, d: date) -> Path:
    return (
        _DATA_DIR
        / table
        / f"year={d.year}"
        / f"month={d.month:02d}"
        / f"day={d.day:02d}"
        / f"school_id={school_id}"
        / f"{table}.parquet"
    )


def _write_parquet(table: str, records: list, school_id: int, d: date) -> None:
    path = _parquet_path(table, school_id, d)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_parquet(path, index=False)


def _load_from_parquet(school_id: int, d: date) -> dict:
    return {
        table: pd.read_parquet(_parquet_path(table, school_id, d)).to_dict("records")
        for table in ("students", "attendance", "contacts")
    }
