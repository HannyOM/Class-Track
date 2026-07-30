# ClassTrack

A Django-based Learning Management System (LMS) MVP for managing courses, assignments, and submissions across two student cohorts (BSSTC and BNTC).

Built with Django 6.x + Bootstrap 5, using SQLite for development.

## Quick Start

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py seed_data
uv run python manage.py runserver
```

Then open http://localhost:8000.

## Demo Accounts

After running `seed_data`:

| Role       | Username   | Password  |
|------------|-----------|-----------|
| Instructor | `INST001` | password  |
| Instructor | `INST002` | password  |
| Student    | `STU001`  | password  |
| Student    | `STU002`  | password  |
| Student    | `STU003`  | password  |

## URLs

| Path | Description |
|------|-------------|
| `/admin/` | Django admin (admin only — create via `createsuperuser`) |
| `/login/` | Login page |
| `/student/dashboard/` | Student dashboard — view assignments, upload & submit |
| `/student/assignment/<id>/` | Assignment detail with file upload |
| `/instructor/dashboard/` | Instructor dashboard — stats, courses, recent submissions |
| `/instructor/courses/` | All course offerings |
| `/instructor/course/create/` | Create a new course (with cohort selection) |
| `/instructor/course/<id>/` | Course detail with assignment list |
| `/instructor/course/<id>/assignment/create/` | Create assignment for a course |
| `/instructor/assignment/<id>/` | View submitted/not-submitted students |

## Creating an Admin Account

```bash
uv run python manage.py createsuperuser
```

Then log in at `/admin/` to manage users, courses, and assignments.

## Running Tests

```bash
uv run python manage.py test
```

## Project Structure

```
accounts/        — Student & Instructor profile models
courses/         — ClassGroup, Course, CourseOffering
assignments/     — Assignment, Submission, file validators
dashboard/       — Student + Instructor dashboard views
templates/       — Bootstrap 5 HTML templates
media/           — Uploaded submission files (dev only)
```

## Tech Stack

- **Django 6.x** — full-stack framework
- **Bootstrap 5** — frontend styling (CDN)
- **SQLite** — local development database
- **UV** — Python package manager
