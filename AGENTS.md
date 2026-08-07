# ClassTrack

## Commands

- **Run dev server:** `uv run python manage.py runserver`
- **Run migrations:** `uv run python manage.py migrate`
- **Create migrations:** `uv run python manage.py makemigrations`
- **Run tests:** `uv run python manage.py test`
- **Shell:** `uv run python manage.py shell`
- **Add dependency:** `uv add <package>`
- **Lint:** `uv run python -m ruff check .`

## Project

ClassTrack is a Django-based Learning Management System (LMS) MVP for a
training program with two student cohorts (**BSSTC** — Basic Space Science and
Technology Course; **BNTC** — Basic Non-Technical Course). The MVP covers only
authentication, course management, assignment management, assignment
submission, and submission tracking.

**Read before writing or editing code:**

- [README.md](./README.md) — setup, quick start, demo accounts.
- [PRD.md](./PRD.md) — product requirements and user workflows.
- [SPEC.md](./SPEC.md) — implemented technical design (data model, views,
  business-rule enforcement, URL routes).

The MVP is already implemented. This file is the operating guide; the PRD and
SPEC carry the full detail. When requirements here conflict with what's in the
repo, prefer the repo unless the design intentionally changed — update this
file and the SPEC in that case.

## Roles & auth

Three roles: **student**, **instructor**, **administrator**. There is no
self-service signup — administrators create all accounts via Django admin.
Students log in with their course/student number and instructors with their
staff number, both as `User.username`. `Student` and `Instructor` profiles hang
off `User` via `OneToOneField` (`related_name="student_profile"` /
`"instructor_profile"`) to distinguish roles.

## Design invariants (do not break)

- **No `password` field on `Student`/`Instructor`** — authentication lives
  entirely on `django.contrib.auth.models.User`.
- **No flat `Course`–`Instructor` many-to-many.** The course–class–instructor
  relationship is expressed through `CourseOffering`. A combined course is one
  `Course` with two offerings (one per cohort, possibly different
  instructors). `CourseOffering.unique_together = ("course", "class_group")`.
- `Assignment` belongs to exactly one `CourseOffering`, so it is inherently
  scoped to one cohort even for a combined course.
- `Submission.unique_together = ("assignment", "student")` — one file per
  submission; `submitted_at` is set only when the student clicks "Submit".
- `ClassGroup` is modeled as rows (not a hardcoded choices field) so a third
  cohort can be added without a business-logic migration.
- Use `timezone.now()` (never `datetime.now()`) for all deadline comparisons;
  `USE_TZ = True`.
- Use `PROTECT`/`CASCADE` on foreign keys exactly as in the existing
  `*/models.py` files; don't casually swap to `SET_NULL`.

## Business rules to enforce (server-side, at view/queryset level)

1. **Class isolation** — a student only sees/accesses assignments whose
   offering's `class_group` matches their own. Cross-cohort access returns
   403/404, not a redirect that leaks info.
2. **Deadline enforcement** — once `timezone.now() >= assignment.deadline`, no
   add-file or submit is accepted; validate in the view, not just the
   template.
3. **File constraints** — reject uploads over 5 MB and any file type other
   than PDF/DOC/DOCX with a clear form error. Client-side is best effort;
   server-side is authoritative.
4. **Ownership** — a student can only view/submit/edit their own submissions;
   an instructor can only manage offerings/assignments/submissions tied to
   their own profile.
5. **One submission per student per assignment** — re-adding a file before the
   deadline updates the existing `Submission` row rather than creating a
   duplicate.
6. **No self-registration** — only an administrator creates users and role
   profiles (via Django admin).
7. **Upload safety** — generate unique filenames on upload and never build a
   storage path from unsanitized client input.

Validate all of the above in views/forms — never rely solely on frontend
restrictions or template-level hiding.

## Out of scope (do not add unless asked)

Self-service registration/signup; password reset via email; grading/scoring;
attendance, notifications, messaging, quizzes, analytics, transcripts;
payments; REST API layer; cloud file storage; multi-file submissions; editing
or deleting a submission after the deadline.

## Coding standards

- Use Django Class-Based Views where they fit cleanly (`ListView`,
  `DetailView`, `CreateView`); fall back to function-based views for anything
  with nontrivial branching (role-based redirect after login, submit-vs-add-file
  distinction).
- Use Django Forms/ModelForms; keep business logic out of templates.
- Use type hints where practical; docstrings for models, views, and any
  service/helper functions.
- Validate file size and type in a reusable validator function, not inline in
  the view, so both the model field and the form use the same check.
- Every view that touches a `CourseOffering`, `Assignment`, or `Submission`
  must filter by the requesting user's role/ownership at the queryset level —
  don't rely on template-level hiding alone.
- Prioritize correctness and simplicity over cleverness; avoid premature
  optimization.
