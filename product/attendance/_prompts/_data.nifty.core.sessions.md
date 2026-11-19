# core.sessions

## What It Is

`core.sessions` is an Ed-Fi standard entity representing a distinct period of instruction at a school — a semester, trimester, or full year. It is part of the academic calendar, not a student record.

Ed-Fi definition: *"A Session is the prescribed span of time when an education institution is open, instruction is provided, and students are under the direction and guidance of teachers and/or education institution administration."*

## Key Columns

| Column | Description |
|---|---|
| `session_name` | Human-readable name, e.g. `"2026-2027 Full Year"` |
| `school_id` | FK to `core.schools` — each school gets its own session row |
| `school_year` | Integer representing the year the school year *ends* (Ed-Fi convention) — e.g. `2027` for the 2026–2027 year |
| `term_descriptor` | Ed-Fi enumerated value: `"Full Year"`, `"Fall Semester"`, `"Spring Semester"`, `"Summer Semester"`, `"Quarter"`, `"Trimester"` |
| `begin_date` | The date the academic session starts for this school |
| `end_date` | The date the academic session ends for this school |
| `total_instructional_days` | Optional count of instructional days in the session |

## Primary Key

`(session_name, school_id, school_year)` — each school has its own session row even when dates are identical across schools.

## How It Is Populated

Manually for now. A future pipeline will pull session data from PowerSchool and keep it current automatically. Do not auto-populate this table from the daily attendance pipeline.

## Why the Pipeline Depends on It

The daily attendance pipeline (Step 3 — transform) reads `begin_date` from `core.sessions` to use as a stand-in `entry_date` on `core.student_school_associations`. See `_data.nifty.core.student_school_associations.md` for why this matters.

If `core.sessions` has no active row for a school on the pipeline's target date, student-school associations for that school are skipped with a warning. The pipeline does not crash, but those students will be missing from `core.student_school_associations` until the sessions table is populated.
