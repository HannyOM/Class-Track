# ClassTrack

## Commands

- **Run dev server:** `uv run python manage.py runserver`
- **Run migrations:** `uv run python manage.py migrate`
- **Create migrations:** `uv run python manage.py makemigrations`
- **Run tests:** `uv run python manage.py test`
- **Shell:** `uv run python manage.py shell`
- **Add dependency:** `uv add <package>`
- **Lint/typecheck:** `uv run python -m ruff check .`




## Student Learning Management System (MVP)

This file gives an AI coding agent (e.g. OpenAI Codex / Codex CLI) everything
needed to build this project from scratch or continue building it. Read this
whole file before writing or editing code. When requirements here conflict
with something already in the repo, this file wins unless the repo has
clearly evolved the design on purpose — in that case, update this file too.

## 1. Project overview

Build a Django-based Learning Management System (LMS) MVP for a training
program with two student cohorts:

- **BSSTC** — Basic Space Science and Technology Course
- **BNTC** — Basic Non-Technical Course

Each cohort takes multiple courses. Some courses are **combined**, meaning
both cohorts take the exact same course together. Courses are taught by
instructors; a single instructor can teach multiple courses to a single
cohort, and can teach in both cohorts. Multiple instructors teach within a
single cohort.

The MVP focuses exclusively on: authentication, course management,
assignment management, assignment submission, and submission tracking.

**Do not implement**: grading/scoring, attendance, notifications,
messaging, quizzes, analytics, transcript generation, or payment
functionality. These are explicitly out of scope — do not add them even
if they seem like natural extensions.

There are three roles: **student**, **instructor**, **administrator**.
There is no public registration flow — accounts are created by an admin
via Django admin, not self-service signup.

## 2. Tech stack

- Django 5.x
- SQLite for local/dev (default `db.sqlite3`); design should not preclude
  swapping to Postgres later (avoid SQLite-only features)
- Django's built-in auth (`django.contrib.auth`) for **everything**
  password- and session-related. Do **not** add a raw `password` field to
  `Student` or `Instructor` — that would bypass Django's password hashing
  and break `authenticate()`/`login()`/permissions entirely. Students log
  in with their course/student number as `User.username`; instructors log
  in with their staff number as `User.username`. Two profile models
  (`Student`, `Instructor`) hang off `User` via `OneToOneField` to
  distinguish roles — `password` lives only on `User`.
- Server-rendered Django templates + **Bootstrap 5** for styling. No
  React, Vue, Angular, or any frontend framework, and no DRF/REST API
  layer for the MVP — keep it simple: Django views + templates + forms.
  Keep the UI simple and clean; polish is not the goal of the MVP.
- Django's `FileField` + local `MEDIA_ROOT` storage for assignment file
  uploads (no S3/cloud storage in the MVP). Store uploads under
  `media/submissions/`.

## 3. Domain model (already designed — implement as-is unless a bug is found)

Entities and relationships:

- `ClassGroup` — the two cohorts (BSSTC, BNTC). Modeled as rows, not a
  hardcoded choices field, so a third cohort could be added later without
  a migration that touches business logic. Fields: `id`, `code`, `name`.
- `Student` — one-to-one with `User`. Fields: `student_id` (unique, ==
  `User.username`), `class_group` (FK to `ClassGroup`), `full_name`,
  `email` (optional). No `password` field — auth lives on `User`.
- `Instructor` — one-to-one with `User`. Fields: `staff_id` (unique, ==
  `User.username`), `full_name`, `email` (optional). No `password` field.
- `Course` — `id`, `course_code`, `title`, `description` (optional). A
  `Course` does **not** carry a class or instructor directly — that
  relationship is expressed through `CourseOffering` below, not a flat
  many-to-many. A flat M2M from `Course` straight to `Instructor` can't
  express "which instructor teaches *which class's* section of a combined
  course," which this program needs (per section 1: an instructor's
  assignment is per course *and* per class).
- `CourseOffering` — the join between `Course`, `ClassGroup`, and
  `Instructor`. This is the actual "class an instructor teaches."
  - A **combined** course = one `Course` with two `CourseOffering` rows
    (one per `ClassGroup`), which may have the same or different
    instructor per cohort.
  - `unique_together = ("course", "class_group")` — a course can only be
    offered once per cohort.
- `Assignment` — belongs to exactly one `CourseOffering` (so it is
  inherently scoped to one cohort, even for a combined course). Fields:
  `title`, `question`, `deadline`, `created_at`.
- `Submission` — belongs to one `Assignment` and one `Student`.
  `unique_together = ("assignment", "student")`. Fields: `file` (max
  5 MB, PDF/DOC/DOCX only, enforced via a validator), `submitted_at`
  (only set when the student clicks "Submit" — adding a file without
  submitting must not count as a submission).

The reference implementation of `models.py` is included in this repo /
provided separately — use it verbatim unless you find a genuine defect.
Do not redesign the schema without flagging why first, and do not
reintroduce a `password` field on `Student`/`Instructor` or a flat
`Course`–`Instructor` M2M — both were considered and rejected (see above).

## 4. Business rules the code MUST enforce

1. **Class isolation**: a student must only ever see/access assignments
   whose `CourseOffering.class_group` matches their own `class_group`.
   BNTC students must get a 403/404 (not a redirect that leaks info) if
   they try to access a BSSTC-only assignment URL directly.
2. **Deadline enforcement**: once `timezone.now() >= assignment.deadline`,
   students can no longer add a file or submit for that assignment. The
   "Add File" / "Submit" controls must be disabled/hidden server-side, not
   just hidden in the template — validate in the view too.
3. **File constraints**: reject uploads over 5 MB, and reject any file
   type other than PDF, DOC, or DOCX, with a clear form error. Enforce
   both client-side (best effort) and server-side (authoritative).
4. **Ownership**: a student can only view/submit/edit their own
   submissions, and can never see another student's submissions. An
   instructor can only view/manage courses, assignments, and submissions
   tied to `CourseOffering`s where
   `instructor == request.user.instructor_profile` — never another
   instructor's courses or submissions.
5. **One submission per student per assignment**: re-adding a file before
   the deadline updates the existing `Submission` row rather than
   creating a duplicate.
6. **No self-registration**: only an administrator (via Django admin)
   creates `User` + `Student`/`Instructor` profiles, assigns students to
   classes, manages courses, resets passwords, and manages assignments.
   No custom admin dashboard is required for the MVP.
7. **Upload safety**: generate unique filenames on upload (don't trust
   the client-provided filename) and prevent path traversal — never build
   a storage path directly from unsanitized user input.
8. Validate all of the above in views/forms, never rely solely on
   frontend restrictions or template-level hiding.

## 5. Required user-facing workflows

### Student
1. Log in with student/course number + password.
2. Dashboard shows all assignments available to the student's class as
   cards, each showing: course title, assignment title, deadline, and
   submission status (Submitted / Not Submitted / Deadline Passed).
3. Each open, not-yet-submitted assignment has an **"Add File"** control
   to attach a file (≤5 MB, PDF/DOC/DOCX) and, separately, a **"Submit"**
   button that finalizes the submission (sets `submitted_at`).
4. Once submitted, show submission status/timestamp instead of the
   add/submit controls. If the deadline has passed and nothing was
   submitted, show it as missed/closed with no upload controls.

### Instructor
1. Log in with staff/instructor number + password.
2. Dashboard shows summary stats: total courses, total assignments,
   recent submissions — plus a **Courses** section listing courses taught.
3. **Create Course**: course code, title, description, then pick which
   class(es) it's for (BSSTC, BNTC, or both — "both" creates two
   `CourseOffering` rows). This creates the `Course` and one or two
   `CourseOffering`s with this instructor.
4. **Create Assignment**: pick one of the instructor's `CourseOffering`s,
   then set title, question, deadline.
5. Clicking a course → list of assignments (by title) under that
   `CourseOffering`.
6. Clicking an assignment title → two lists:
   - **Submitted students**: name, course number, submission timestamp,
     download link.
   - **Not submitted students**: name, course number.
   Both lists are scoped to students in that `CourseOffering`'s
   `class_group` only.

### Administrator (Django admin — no custom UI needed)
Create student accounts, create instructor accounts, assign students to
classes, manage courses, reset passwords, manage assignments.

## 6. Suggested Django app structure

```
lms_project/
  manage.py
  lms_project/            # Django project package (settings, urls, wsgi/asgi)
  accounts/                # Student & Instructor profile models, authentication
    models.py
    views.py               # login/logout, role-based redirect after login
    urls.py
  courses/                 # Course, ClassGroup, CourseOffering
    models.py
    views.py
    urls.py
  assignments/              # Assignment, Submission
    models.py
    forms.py                # SubmissionForm with 5MB + filetype validators
    views.py
    urls.py
  dashboard/                # Student dashboard, Instructor dashboard
    views.py
    urls.py
  templates/
    accounts/
    courses/
    assignments/
    dashboard/
    base.html                # Bootstrap 5 base layout
  static/
  media/
    submissions/             # uploaded submission files (dev only)
```

A single app is also acceptable for an MVP if the agent prefers less
ceremony — prioritize working software over perfect app boundaries, but
keep models/views/urls organized by domain concept either way.

## 7. URL structure

```
/login/
/student/dashboard/
/student/assignment/<id>/

/instructor/dashboard/
/instructor/courses/
/instructor/course/<id>/
/instructor/course/<id>/assignment/create/
/instructor/assignment/<id>/
/instructor/course/create/
```

## 8. Build order (do these in sequence, committing/testing after each)

1. Scaffold the Django project + one settings module (dev settings only
   is fine for MVP: `DEBUG=True`, SQLite, local media storage).
2. Add `ClassGroup`, `Student`, `Instructor`, `Course`, `CourseOffering`,
   `Assignment`, `Submission` models (per section 3). Run
   `makemigrations` + `migrate`.
3. Register all models in `admin.py` so accounts and courses can be
   created/inspected without building forms first.
4. Seed data: management command or fixture that creates the two
   `ClassGroup` rows (BSSTC, BNTC) plus a couple of demo students,
   instructors, courses, and offerings for manual testing.
5. Auth: login view (single login form; after auth, redirect based on
   whether the user has a `student_profile` or `instructor_profile`),
   logout view. Use Django's `LoginView`/`LogoutView` where possible
   rather than hand-rolling session handling.
6. Student dashboard view + template (section 5, Student workflow).
7. Submission create/update view enforcing rules in section 4 (class
   isolation, deadline, file size/type, ownership, upload safety).
8. Instructor: Create Course view/form (course + class-group selection).
9. Instructor: Create Assignment view/form (scoped to that instructor's
   own `CourseOffering`s only).
10. Instructor dashboard: summary stats, Courses list → Assignments list
    → Submitted/Not-submitted view (section 5, Instructor workflow).
11. Write tests for the rules in section 4 first — they're the parts most
    likely to have security/logic bugs (class isolation and ownership
    checks especially). Use Django's `TestCase` + `Client`.
12. `README.md` with setup steps (`pip install`, `migrate`,
    `createsuperuser`, `runserver`) and a short note on how to seed demo
    data.

## 9. Explicitly out of scope for this MVP (do not build unless asked)

- Self-service registration/signup
- Password reset via email
- Grading/scoring of assignments
- Attendance, notifications, messaging, quizzes, analytics, transcripts
- Payment functionality
- REST API layer
- Cloud file storage
- Multi-file submissions (one file per submission for MVP)
- Editing/deleting a submission after the deadline

## 10. Coding standards

- Use Django Class-Based Views where they fit cleanly (`ListView`,
  `DetailView`, `CreateView`); fall back to function-based views for
  anything with nontrivial branching (e.g. role-based redirect after
  login, submit-vs-add-file distinction).
- Use Django Forms and `ModelForm`s; keep business logic out of templates.
- Use type hints where practical, and docstrings for models, views, and
  any service/helper functions.
- Use Django's `timezone.now()` (not `datetime.now()`) for all deadline
  comparisons — `USE_TZ = True`.
- Use `unique_together`/`UniqueConstraint` and `PROTECT`/`CASCADE`
  choices exactly as specified in section 3; don't casually swap to
  `SET_NULL`.
- Validate file size and type in a reusable validator function, not
  inline in the view, so both the model field and the form use the same
  check.
- Every view that touches a `CourseOffering`, `Assignment`, or
  `Submission` must filter by the requesting user's role/ownership at the
  queryset level — don't rely on template-level hiding alone.
- Prioritize correctness and simplicity over cleverness; avoid premature
  optimization.

## 11. Deliverables

Generate: Django project structure, models, migrations, forms, views,
URLs, templates, admin configuration, authentication flow, file upload
handling (with size/type/path-safety checks), permission checks, and
sample seed data.

## 12. MVP success criteria

**A student can**: log in, view assignments for their class, upload an
assignment file, submit before the deadline.

**An instructor can**: log in, create a course, create an assignment,
view submissions, identify who submitted and who did not.

**An administrator can**: create students, create instructors, manage
classes, manage courses (via Django admin).

The application must be runnable locally using:

```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

If all workflows above function correctly and the business rules in
section 4 are enforced at the view/queryset level, the MVP is complete.
