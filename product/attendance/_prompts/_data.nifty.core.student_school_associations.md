# core.student_school_associations

## What It Is

`core.student_school_associations` is an Ed-Fi standard entity that links a specific student to a specific school for a specific enrollment period. It is a student record, not a calendar record.

## Key Columns

| Column | Description |
|---|---|
| `student_unique_id` | FK to `core.students` |
| `school_id` | FK to `core.schools` |
| `entry_date` | The date this specific student enrolled at this school |
| `entry_grade_level_descriptor` | Ed-Fi grade string, e.g. `"Ninth grade"`, `"Tenth grade"` |
| `exit_withdraw_date` | The date the student left — NULL if still enrolled |
| `primary_school` | Boolean — TRUE if this is the student's main school |

## Primary Key

`(student_unique_id, school_id, entry_date)` — `entry_date` is part of the key because a student can leave and re-enroll, producing multiple rows with different entry dates.

## entry_date vs sessions.begin_date

These look like the same value but represent different things:

- **`sessions.begin_date`** — when the *school year* starts. A property of the academic calendar, shared by all students at that school.
- **`student_school_associations.entry_date`** — when *this student* enrolled at this school. A property of the individual student-school relationship.

They are often identical — most students enroll on the first day of school. But they diverge for:
- **Transfer students** — `entry_date` is mid-year, long after `sessions.begin_date`
- **Re-enrollment** — a student who left and came back gets a new row with a new `entry_date`

## Current Stand-In Behavior

The PowerSchool API does not return enrollment dates in the current spoofed implementation. Until real PS credentials are wired in, the pipeline borrows `sessions.begin_date` as `entry_date`. This is noted in `transform.py` and should be replaced with the actual PS enrollment date field (`students.enroll_status` date or equivalent) when available.

## Downstream Impact

`core.student_school_associations` is used to confirm a student is actively enrolled at a school before sending an absence notification. A student with no association row (e.g., because `core.sessions` was empty) will not appear in the absent student list even if they have an attendance event.
