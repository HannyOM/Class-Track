# ClassTrack — Product Requirements Document (PRD)

| | |
|---|---|
| **Status** | Implemented (MVP complete) |
| **Product** | ClassTrack LMS |
| **Version** | 1.0 |
| **Companion documents** | [SPEC.md](./SPEC.md) (technical), [README.md](./README.md) (setup), [AGENTS.md](./AGENTS.md) (agent guidance) |

---

## 1. Executive summary

ClassTrack is a web-based **Learning Management System (LMS)** for a training
program. It lets administrators and instructors publish courses and
assignments to two student cohorts, and lets students upload and submit their
work before a deadline.

The MVP deliberately covers only five areas: **authentication, course
management, assignment management, assignment submission, and submission
tracking.** Everything else (grading, attendance, messaging, etc.) is
explicitly out of scope so the team can validate the core workflow quickly.

## 2. Background & problem statement

The training program runs two simultaneous student cohorts:

- **BSSTC** — Basic Space Science and Technology Course
- **BNTC** — Basic Non-Technical Course

Both cohorts are taught in parallel. Some courses are taught to a single
cohort; others are **combined** (the same course taught to both cohorts,
possibly by different instructors). Currently the program has no central place
to publish assignments, collect student submissions, and tell instructors who
has and has not submitted.

The problem to solve: give each role a simple, reliable way to manage the
assignment lifecycle, with strict guarantees that a student only ever sees
their own class's work and that submissions are impossible after the deadline.

## 3. Goals & non-goals

### Goals (MVP)

1. A student can log in, see every assignment for their cohort, attach a file,
   and submit before the deadline — once.
2. An instructor can log in, create a course (for one or both cohorts), create
   assignments against that course, and see exactly which students submitted
   and which did not.
3. An administrator can create student/instructor accounts, assign students to
   cohorts, and manage courses via Django admin.
4. Enforce, at the server level: class isolation, deadline enforcement, file
   type/size limits, ownership, and upload path safety.

### Non-goals (explicitly out of scope for the MVP)

- Self-service registration/signup
- Password reset via email
- Grading/scoring of assignments
- Attendance, notifications, messaging, quizzes, analytics, transcripts
- Payment functionality
- REST API layer
- Cloud file storage
- Multi-file submissions (one file per submission)
- Editing/deleting a submission after the deadline

## 4. Target users & roles

### 4.1 Student
- Has a course/student number (e.g. `STU001`) used as login username.
- Belongs to exactly one cohort (BSSTC or BNTC).
- Needs: see their assignments, upload a file, submit before the deadline,
  check their submission status.

### 4.2 Instructor
- Has a staff/instructor number (e.g. `INST001`) used as login username.
- Teaches one or more course-cohort sections (offerings).
- Needs: create courses and assignments for their own offerings, review
  submissions, see who has not submitted.

### 4.3 Administrator
- Full control via the Django admin site.
- Needs: create users and role profiles, assign students to cohorts, manage
  courses/offerings, reset passwords, manage assignments.

There is **no public registration**. Accounts are provisioned by an
administrator only.

## 5. Product scope

### In scope
- Login / logout (single login page, role-based redirect after login).
- Student dashboard listing all assignments available to the student's cohort.
- Student assignment detail page with "Add File" and "Submit" controls.
- Instructor dashboard with summary stats and recent submissions.
- Course creation with cohort selection (one cohort or both).
- Assignment creation scoped to an instructor's own offerings.
- Course → assignments → submitted/not-submitted drill-down.
- Django admin registration for all models.

### Out of scope (see §3 Non-goals)

## 6. User stories & workflows

### 6.1 Student

| ID | User story | Status |
|----|-----------|--------|
| ST-1 | As a student, I can log in with my course number so that I can access my assignments. | Implemented |
| ST-2 | As a student, I see a dashboard of every assignment for my cohort, each showing course title, assignment title, deadline, and status (Submitted / Not Submitted / Deadline Passed). | Implemented |
| ST-3 | As a student, for an open assignment I can attach a file (PDF/DOC/DOCX, ≤ 5 MB) using **Add File**, without it counting as a submission. | Implemented |
| ST-4 | As a student, I can press **Submit** to finalize my submission (records `submitted_at`). | Implemented |
| ST-5 | As a student, I can re-upload a file before the deadline; it updates my existing draft rather than creating a duplicate. | Implemented |
| ST-6 | As a student, once submitted I see my submission timestamp and download link, not the upload controls. | Implemented |
| ST-7 | As a student, if the deadline has passed and I did not submit, I see the assignment as closed/missed with no upload controls. | Implemented |
| ST-8 | As a student, I can never see or access assignments from a different cohort, nor other students' submissions. | Implemented |

### 6.2 Instructor

| ID | User story | Status |
|----|-----------|--------|
| IN-1 | As an instructor, I can log in with my staff number. | Implemented |
| IN-2 | As an instructor, my dashboard shows totals for course offerings and assignments, a list of my courses, and my recent submissions. | Implemented |
| IN-3 | As an instructor, I can **Create Course** with code, title, description, and pick one or both cohorts — "both" creates two offerings. | Implemented |
| IN-4 | As an instructor, I can **Create Assignment** for one of my own offerings (title, question, deadline). | Implemented |
| IN-5 | As an instructor, clicking a course lists its assignments. | Implemented |
| IN-6 | As an instructor, clicking an assignment shows two lists — **Submitted** (name, course number, timestamp, download) and **Not Submitted** (name, course number) — scoped to the offering's cohort. | Implemented |
| IN-7 | As an instructor, I can only see my own offerings, courses, assignments, and their submissions. | Implemented |

### 6.3 Administrator

| ID | User story | Status |
|----|-----------|--------|
| AD-1 | As an administrator, I can create student accounts and instructor accounts. | Implemented (Django admin) |
| AD-2 | As an administrator, I can assign students to cohorts. | Implemented |
| AD-3 | As an administrator, I can manage courses/offerings and reset passwords. | Implemented |
| AD-4 | As an administrator, I can inspect assignments and submissions. | Implemented |

## 7. Functional requirements

- **FR-1 (Auth):** Single login form authenticating against Django's built-in
  auth. After login, users are redirected to their role dashboard based on
  whether they have a student or instructor profile. Logout via POST.
- **FR-2 (Student dashboard):** List every `Assignment` belonging to a
  `CourseOffering` whose `class_group` matches the student's cohort, ordered by
  deadline (newest deadline first, per course), with status computed from
  `submitted_at` and `deadline`.
- **FR-3 (Add File / Submit):** On the student assignment detail page, `Add
  File` saves the file without setting `submitted_at`; `Submit` saves the file
  and sets `submitted_at = timezone.now()`.
- **FR-4 (Draft re-upload):** Posting a file on an existing draft updates the
  single `Submission` row (`unique_together = assignment, student`).
- **FR-5 (Instructor dashboard):** Show offering count, assignment count
  (aggregated across the instructor's offerings), course list, and up to 10
  recent submissions from the instructor's offerings.
- **FR-6 (Create course):** Form captures course code/title/description plus a
  multi-select of cohorts; saving creates the `Course` and one `CourseOffering`
  per selected cohort with the current instructor.
- **FR-7 (Create assignment):** Form is scoped to the instructor's own
  offerings; saving creates an `Assignment` under the selected offering.
- **FR-8 (Submission review):** Assignment detail shows every student in the
  offering's cohort partitioned into submitted (with timestamp + download link)
  and not-submitted.
- **FR-9 (Admin):** All models registered and searchable/filterable in Django
  admin.

## 8. Business rules (product level)

The following rules are requirements the product must guarantee. The technical
enforcement of each is specified in [SPEC.md §5](./SPEC.md#5-business-rules--enforcement-points).

1. **Class isolation** — a student only ever sees/accesses assignments whose
   offering's cohort matches their own. Cross-cohort access returns 403/404, not
   a redirect that leaks information.
2. **Deadline enforcement** — once `timezone.now() >= assignment.deadline`, no
   add-file or submit is accepted; controls are hidden *and* the server rejects
   the POST.
3. **File constraints** — uploads > 5 MB, or anything other than PDF/DOC/DOCX,
   are rejected with a clear form error. Enforced client-side (best effort) and
   server-side (authoritative).
4. **Ownership** — a student can only view/submit/edit their own submissions;
   an instructor can only manage offerings/assignments/submissions tied to
   their own profile.
5. **One submission per student per assignment** — re-adding a file before the
   deadline updates the existing `Submission` row.
6. **No self-registration** — only an administrator creates accounts via
   Django admin.
7. **Upload safety** — uploaded files get server-generated unique names; the
   client-provided filename is never trusted for storage paths.

## 9. Non-functional requirements

- **Security** — all authorization enforced at the view/queryset level, never
  template hiding alone; passwords managed exclusively by
  `django.contrib.auth`.
- **Usability** — server-rendered pages styled with Bootstrap 5; simple, clean
  UI; polish is not a goal of the MVP.
- **Portability** — SQLite for local/dev; no SQLite-only features so the schema
  can move to Postgres later.
- **Correctness** — all deadline comparisons use Django `timezone.now()` with
  `USE_TZ = True`.
- **Simplicity** — no frontend framework, no REST API; prioritizes working
  software over architectural ceremony.

## 10. MVP success criteria

The MVP is complete when:

- A **student** can log in, view their cohort's assignments, upload a file, and
  submit before the deadline.
- An **instructor** can log in, create a course, create an assignment, view
  submissions, and identify who did and did not submit.
- An **administrator** can create students and instructors, manage classes and
  courses (via Django admin).
- All business rules in §8 are enforced at the view/queryset level.

All of the above are implemented and covered by an automated test suite
(see [SPEC.md §13](./SPEC.md#13-testing)).

## 11. Future enhancements (not in MVP scope)

- **Auth-gated file downloads** — media files are currently served publicly by
  URL in dev; a `@login_required` view streaming submissions via
  `FileResponse` (verifying instructor ownership of the assignment's offering)
  is the natural next step.
- **Grading / marking** — add a score and optional feedback to `Submission`.
- Password reset flow, notifications, attendance, analytics, transcripts, REST
  API, and cloud storage remain out of scope.

## 12. References

- [SPEC.md](./SPEC.md) — technical specification of the implemented system.
- [README.md](./README.md) — setup instructions and demo accounts.
- [AGENTS.md](./AGENTS.md) — guidance for AI coding agents working on this repo.
