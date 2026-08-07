# ClassTrack — Technical Specification (SPEC)

| | |
|---|---|
| **Status** | Implemented (MVP complete) |
| **Product** | ClassTrack LMS |
| **Version** | 1.0 |
| **Companion documents** | [PRD.md](./PRD.md) (requirements), [README.md](./README.md) (setup), [AGENTS.md](./AGENTS.md) (agent guidance) |

This document is the technical specification of what **has been built**. It
describes the implemented architecture, data model, business-rule enforcement
points, and engineering conventions, so that a developer (human or AI) can
understand the system and extend it consistently.

---

## 1. Overview

ClassTrack is a server-rendered Django application for managing courses,
assignments, and student submissions across two cohorts (BSSTC and BNTC). It
uses Django's built-in auth, function-based views, Django forms, Bootstrap 5
templates, SQLite storage, and local file storage for submissions.

The repository layout:

```
classtrack/          Django project package (settings, urls, wsgi/asgi)
accounts/            Student & Instructor profile models + auth views
courses/             ClassGroup, Course, CourseOffering models
assignments/         Assignment, Submission models, validators, forms
dashboard/           Student + Instructor dashboard views
core/                Seed-data management command (utility app)
templates/           Bootstrap 5 HTML templates
static/              Static assets
media/submissions/   Uploaded submission files (dev only)
```

## 2. Tech stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Language | Python ≥ 3.12 | `requires-python = ">=3.12"` |
| Framework | Django ≥ 6.0.7 | `django>=6.0.7` in `pyproject.toml` |
| Package manager | UV | `uv add`, `uv run`, `uv sync` |
| Database | SQLite (`db.sqlite3`) | Schema avoids SQLite-only features for later Postgres move |
| Frontend | Server-rendered templates + Bootstrap 5 (CDN) | No JS framework, no REST API |
| File storage | Local `FileField`, `MEDIA_ROOT = media/` | Uploads under `media/submissions/` |
| Linting | Ruff | `uv run python -m ruff check .` |

## 3. Application architecture

### 3.1 Django apps

| App | Responsibility | Key contents |
|-----|----------------|--------------|
| `accounts` | Role profiles + authentication | `Student`, `Instructor` models; `CustomLoginView` |
| `courses` | Cohorts and course structure | `ClassGroup`, `Course`, `CourseOffering`; `CourseCreateForm` |
| `assignments` | Assignment lifecycle | `Assignment`, `Submission`; validators; `SubmissionForm`, `AssignmentCreateForm` |
| `dashboard` | Role dashboards + drill-down | `student_dashboard`, `student_assignment_detail`, `instructor_dashboard`, `instructor_course_detail`, `instructor_assignment_detail` |
| `core` | Utilities | `seed_data` management command |
| `classtrack` | Project configuration | `settings.py`, root `urls.py` |

### 3.2 Request flow

1. Protected views redirect unauthenticated users to `/login/` via
   `@login_required`; `/` itself has no landing page (see §14).
2. `CustomLoginView` authenticates against `django.contrib.auth` and redirects
   to `/student/dashboard/` or `/instructor/dashboard/` based on whether the
   user has a `student_profile` or `instructor_profile`.
3. Every view is protected with `@login_required` and scopes its querysets to
   the requesting user's profile (see §5).
4. Templates render via `templates/base.html`, which provides the Bootstrap 5
   navbar, messages, and a logout (POST) button.

## 4. Data model

All models are defined in `accounts/models.py`, `courses/models.py`, and
`assignments/models.py`. Migrations are applied and current.

### 4.1 `accounts.Student`

One-to-one with `User`. **No password field** — authentication lives entirely
on `User`.

| Field | Type | Constraints |
|-------|------|-------------|
| `user` | `OneToOneField(User)` | `related_name="student_profile"`, `on_delete=CASCADE` |
| `student_id` | `CharField(20)` | `unique`; equals `User.username` |
| `class_group` | `FK(ClassGroup)` | `related_name="students"`, `on_delete=PROTECT` |
| `full_name` | `CharField(255)` | required |
| `email` | `EmailField` | optional (`blank=True`) |

### 4.2 `accounts.Instructor`

One-to-one with `User`. **No password field.**

| Field | Type | Constraints |
|-------|------|-------------|
| `user` | `OneToOneField(User)` | `related_name="instructor_profile"`, `on_delete=CASCADE` |
| `staff_id` | `CharField(20)` | `unique`; equals `User.username` |
| `full_name` | `CharField(255)` | required |
| `email` | `EmailField` | optional (`blank=True`) |

### 4.3 `courses.ClassGroup`

The cohorts, stored as **rows**, not a hardcoded choices field, so a third
cohort can be added later without a business-logic migration.

| Field | Type | Constraints |
|-------|------|-------------|
| `code` | `CharField(20)` | `unique` (e.g. `BSSTC`, `BNTC`) |
| `name` | `CharField(255)` | e.g. "Basic Space Science and Technology Course" |

### 4.4 `courses.Course`

| Field | Type | Constraints |
|-------|------|-------------|
| `course_code` | `CharField(20)` | `unique` |
| `title` | `CharField(255)` | required |
| `description` | `TextField` | optional (`blank=True`) |

A `Course` does **not** carry a class or instructor directly — that
relationship lives in `CourseOffering`, which lets a combined course express a
different instructor per cohort.

### 4.5 `courses.CourseOffering`

The join between `Course`, `ClassGroup`, and `Instructor`. This is "the class
an instructor teaches." A combined course = one `Course` with two offerings
(one per cohort), possibly with different instructors.

| Field | Type | Constraints |
|-------|------|-------------|
| `course` | `FK(Course)` | `related_name="offerings"`, `on_delete=CASCADE` |
| `class_group` | `FK(ClassGroup)` | `related_name="offerings"`, `on_delete=PROTECT` |
| `instructor` | `FK(Instructor)` | `related_name="offerings"`, `on_delete=PROTECT` |

Model constraints: `unique_together = ("course", "class_group")` — a course is
offered at most once per cohort.

### 4.6 `assignments.Assignment`

Belongs to exactly one `CourseOffering`, so it is inherently scoped to one
cohort even for a combined course.

| Field | Type | Constraints |
|-------|------|-------------|
| `course_offering` | `FK(CourseOffering)` | `related_name="assignments"`, `on_delete=CASCADE` |
| `title` | `CharField(255)` | required |
| `question` | `TextField` | required |
| `deadline` | `DateTimeField` | required |
| `created_at` | `DateTimeField` | `auto_now_add=True` |

Model ordering: `["-deadline"]`.

### 4.7 `assignments.Submission`

One row per (assignment, student). A file can exist without counting as a
submission — `submitted_at` is only set when the student clicks **Submit**.

| Field | Type | Constraints |
|-------|------|-------------|
| `assignment` | `FK(Assignment)` | `related_name="submissions"`, `on_delete=CASCADE` |
| `student` | `FK(Student)` | `related_name="submissions"`, `on_delete=CASCADE` |
| `file` | `FileField` | `upload_to=submission_upload_path`; validators: extension + size |
| `submitted_at` | `DateTimeField` | `null=True, blank=True` |

Model constraints: `unique_together = ("assignment", "student")`. Ordering:
`["-submitted_at"]`.

**Upload path** (`assignments/models.py`):

```python
def submission_upload_path(instance, filename: str) -> str:
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    return f"submissions/assignment_{instance.assignment_id}_student_{instance.student_id}.{ext}"
```

The path is built from the `Submission`'s own DB keys, never from the
client-provided filename. Django additionally appends a random suffix
(`<random>.<ext>`) when a filename collision occurs, guaranteeing unique stored
names (e.g. `assignment_1_student_1_0RHVGc1.pdf`).

## 5. Business rules & enforcement points

Each PRD business rule maps to concrete server-side enforcement.

| # | Rule | Enforcement |
|---|------|-------------|
| 1 | **Class isolation** | `dashboard.views.student_dashboard` filters offerings by `class_group=student.class_group`. `student_assignment_detail` uses `get_object_or_404(Assignment, id=..., course_offering__class_group=student.class_group)` → cross-cohort access is a 404. |
| 2 | **Deadline enforcement** | View computes `deadline_passed = timezone.now() >= assignment.deadline`. When true: the form is not constructed (`form = None`), the template renders a "Deadline has passed" block, and a POST is ignored (`if request.method == "POST" and not deadline_passed`). |
| 3 | **File constraints** | `assignments/validators.py` defines `validate_file_extension` (`.pdf/.doc/.docx`) and `validate_file_size` (≤ 5 MB). Both are attached to `Submission.file` model field *and* invoked in `SubmissionForm.clean_file`; the template `FileInput` also sets `accept` as a best-effort client-side hint. |
| 4 | **Ownership** | Student submission queries always filter `student=request.user.student_profile`. Instructor views filter at the queryset level: `instructor.offerings`, `CourseOffering.objects.filter(instructor=...)`, and `Assignment.objects.filter(course_offering__instructor=...)` → foreign instructor data is a 404. |
| 5 | **One submission per assignment** | `unique_together` on the model; the view passes `instance=submission` to `SubmissionForm`, so re-posting updates the existing row instead of creating a duplicate. |
| 6 | **No self-registration** | No signup views or URLs exist. All account/profile management is via Django admin. |
| 7 | **Upload safety** | Unique names generated server-side via `submission_upload_path` + Django's collision suffix (see §4.7). Storage paths are never built from raw user input. |

All checks are performed in views/forms; nothing relies on template hiding
alone.

## 6. Authentication & authorization

- Uses `django.contrib.auth` end-to-end; passwords live only on `User`.
- `accounts/urls.py`:
  - `login/` → `CustomLoginView` (`accounts.views.CustomLoginView`,
    subclasses Django's `LoginView`, template `accounts/login.html`).
  - `logout/` → Django's `LogoutView(next_page="/login/")`.
- Role detection after login: presence of `request.user.student_profile` or
  `request.user.instructor_profile` drives the redirect target
  (`CustomLoginView.get_redirect_url`).
- All dashboard/course/assignment views are wrapped with `@login_required`;
  `LOGIN_URL = "/login/"`.
- Access control is per-role at the queryset level (see §5), including 404 for
  cross-class and cross-instructor access.

## 7. URL routing

All non-admin routes are included at the project root in `classtrack/urls.py`
(plus `admin/` and dev-time `MEDIA_URL` static serving).

| Route | View | Access |
|-------|------|--------|
| `/login/` | `CustomLoginView` | public |
| `/logout/` | `LogoutView` | authenticated (POST) |
| `/admin/` | Django admin | staff/superuser |
| `/student/dashboard/` | `dashboard.views.student_dashboard` | student |
| `/student/assignment/<int:assignment_id>/` | `dashboard.views.student_assignment_detail` | student |
| `/instructor/dashboard/` | `dashboard.views.instructor_dashboard` | instructor |
| `/instructor/courses/` | `courses.views.instructor_course_list` | instructor |
| `/instructor/course/create/` | `courses.views.instructor_course_create` | instructor |
| `/instructor/course/<int:offering_id>/` | `dashboard.views.instructor_course_detail` | instructor (own offering) |
| `/instructor/course/<int:offering_id>/assignment/create/` | `assignments.views.instructor_assignment_create` | instructor (own offering) |
| `/instructor/assignment/<int:assignment_id>/` | `dashboard.views.instructor_assignment_detail` | instructor (own assignment) |

Note: `instructor/course/<id>/` takes the **offering** PK (per-offering
drill-down), not the `Course` PK.

## 8. Forms

| Form | File | Purpose / behavior |
|------|------|--------------------|
| `SubmissionForm` | `assignments/forms.py` | ModelForm over `Submission` (field `file`); `clean_file` runs extension + size validators; `FileInput` with `accept=".pdf,.doc,.docx"`. |
| `AssignmentCreateForm` | `assignments/forms_instructor.py` | ModelForm over `Assignment`; restricts `course_offering` queryset to the instructor's own offerings; `datetime-local` widget for deadline. |
| `CourseCreateForm` | `courses/forms.py` | ModelForm over `Course` plus a `ModelMultipleChoiceField` for cohorts; `save()` creates the `Course` and one `CourseOffering` per selected cohort with the current instructor. |

## 9. Templates & UI

Base layout: `templates/base.html` — Bootstrap 5.3 (CDN), dark navbar with
user name, logout button (POST form), Django `messages` alerts, `{% block content %}`.

| Template | Route/role |
|----------|-----------|
| `accounts/login.html` | Login card |
| `student/dashboard.html` | Assignment cards with status badges |
| `student/assignment_detail.html` | Assignment details + Add File / Submit form, or submitted / deadline-passed states |
| `instructor/dashboard.html` | Stats, My Courses, Recent Submissions |
| `instructor/course_list.html` | List of the instructor's offerings |
| `instructor/course_form.html` | Create Course |
| `instructor/course_detail.html` | Course → assignment list + Create Assignment link |
| `instructor/assignment_form.html` | Create Assignment |
| `instructor/assignment_detail.html` | Submitted / Not Submitted lists |

Status badges on the student dashboard: `Submitted` (success), `Not Submitted`
(warning), `Deadline Passed` (danger).

## 10. Admin configuration

All seven models are registered with `list_display`, `search_fields`, and/or
`list_filter`:

- `accounts/admin.py` — `Student`, `Instructor`
- `courses/admin.py` — `ClassGroup`, `Course`, `CourseOffering`
- `assignments/admin.py` — `Assignment`, `Submission`

This satisfies the administrator workflow (create accounts, assign cohorts,
manage courses, reset passwords) without a custom admin dashboard.

## 11. Seeding & dev data

`core/management/commands/seed_data.py` (`uv run python manage.py seed_data`) is
idempotent (`get_or_create`) and creates:

- Cohorts: BSSTC, BNTC.
- Instructors: `INST001` / `INST002` (password `password`).
- Courses: MATH101, PHY101, COM101 (combined — one offering per cohort).
- Students: `STU001`, `STU002` (BSSTC), `STU003` (BNTC) (password `password`).
- Assignments: a future-deadline and a past-deadline assignment for BSSTC, and
  a future-deadline assignment for BNTC.

Demo account table: [README.md](./README.md#demo-accounts).

## 12. Settings highlights (`classtrack/settings.py`)

- `INSTALLED_APPS`: Django defaults + `core`, `accounts`, `courses`,
  `assignments`, `dashboard`.
- `DEBUG = True`, SQLite database, `USE_TZ = True`, `TIME_ZONE = 'UTC'`.
- `MEDIA_URL = 'media/'`, `MEDIA_ROOT = BASE_DIR / 'media'`.
- `STATICFILES_DIRS = [BASE_DIR / 'static']`.
- `LOGIN_URL = '/login/'`.

## 13. Testing

Test suite: `assignments/tests.py` (11 tests, Django `TestCase` + `Client`).
Run with `uv run python manage.py test`. Lint with `uv run python -m ruff check .`.

Coverage of business rules:

| Test | Rule |
|------|------|
| `test_student_sees_only_own_class_assignments` | Class isolation (dashboard) |
| `test_bntc_student_gets_404_for_bsstc_assignment` | Class isolation (detail URL) |
| `test_submission_after_deadline_is_blocked` | Deadline (no controls rendered) |
| `test_cannot_post_after_deadline` | Deadline (POST rejected) |
| `test_reject_invalid_file_extension` | File type |
| `test_reject_oversized_file` | File size |
| `test_form_rejects_invalid_file` | File type via form/HTTP |
| `test_student_cannot_see_other_student_submission` | Ownership |
| `test_reupload_updates_existing_submission` | One submission per assignment |
| `test_instructor_see_only_own_offerings` | Instructor ownership (dashboard) |
| `test_instructor_cannot_view_another_instructors_assignment` | Instructor ownership (detail) |

## 14. Known limitations & future work

- **Media served publicly in dev** — in `DEBUG`, `static(settings.MEDIA_URL)`
  serves submission files without auth. A `@login_required` view streaming via
  `FileResponse` (verifying the instructor owns the assignment's offering)
  is the recommended fix before any shared deployment.
- **Role-based view guarding** — views assume `request.user.student_profile` /
  `instructor_profile` exist; a user of the wrong type hitting a role's URL
  raises `RelatedObjectDoesNotExist` rather than a clean 403.
- **No root landing page** — `/` has no URL pattern; the login page is the
  entry point (the base template navbar links to `/`).
- **Grading/marking, notifications, analytics, transcripts** — deliberately
  out of scope (see [PRD.md §3](./PRD.md#3-goals--non-goals)).

## 15. Deviations from the original design brief

| Brief (`AGENTS.md` v1) | Implemented |
|-------------------------|-------------|
| Django 5.x | Django 6.0.7+ |
| Project package `lms_project/` | Project package `classtrack/` |
| Apps `accounts`, `courses`, `assignments`, `dashboard` | Same, plus an empty `core` app hosting the `seed_data` command |
| — | `instructor/course/<id>/` takes the `CourseOffering` PK (offering drill-down) |

The domain model and all business rules were implemented as specified.
