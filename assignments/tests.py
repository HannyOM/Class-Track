from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from accounts.models import Instructor, Student
from assignments.models import Assignment, Submission
from assignments.validators import validate_file_extension, validate_file_size
from courses.models import ClassGroup, Course, CourseOffering


class BusinessRulesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.bsstc = ClassGroup.objects.create(code="BSSTC", name="BSSTC")
        cls.bntc = ClassGroup.objects.create(code="BNTC", name="BNTC")

        user_inst = User.objects.create_user(username="INST01", password="pass")
        cls.instructor = Instructor.objects.create(
            user=user_inst, staff_id="INST01", full_name="Inst One"
        )

        user_s1 = User.objects.create_user(username="STU01", password="pass")
        cls.student_bsstc = Student.objects.create(
            user=user_s1, student_id="STU01", class_group=cls.bsstc, full_name="S1 BSSTC"
        )
        user_s2 = User.objects.create_user(username="STU02", password="pass")
        cls.student_bntc = Student.objects.create(
            user=user_s2, student_id="STU02", class_group=cls.bntc, full_name="S2 BNTC"
        )

        cls.course = Course.objects.create(course_code="C101", title="Course 1")
        cls.offering_bsstc = CourseOffering.objects.create(
            course=cls.course, class_group=cls.bsstc, instructor=cls.instructor
        )
        cls.offering_bntc = CourseOffering.objects.create(
            course=cls.course, class_group=cls.bntc, instructor=cls.instructor
        )

        cls.future_deadline = timezone.now() + timedelta(days=7)
        cls.past_deadline = timezone.now() - timedelta(days=1)

        cls.assignment_bsstc = Assignment.objects.create(
            course_offering=cls.offering_bsstc,
            title="BSSTC Only",
            question="test",
            deadline=cls.future_deadline,
        )
        cls.assignment_past = Assignment.objects.create(
            course_offering=cls.offering_bsstc,
            title="Past Deadline",
            question="test",
            deadline=cls.past_deadline,
        )

    def _make_pdf(self, name="test.pdf"):
        return SimpleUploadedFile(name, b"%PDF-1.4 mock content", content_type="application/pdf")

    # --- Class isolation ---
    def test_student_sees_only_own_class_assignments(self):
        self.client.login(username="STU01", password="pass")
        resp = self.client.get("/student/dashboard/")
        self.assertContains(resp, "BSSTC Only")
        self.client.logout()

        self.client.login(username="STU02", password="pass")
        resp = self.client.get("/student/dashboard/")
        self.assertNotContains(resp, "BSSTC Only")

    def test_bntc_student_gets_404_for_bsstc_assignment(self):
        self.client.login(username="STU02", password="pass")
        resp = self.client.get(f"/student/assignment/{self.assignment_bsstc.id}/")
        self.assertEqual(resp.status_code, 404)

    # --- Deadline enforcement ---
    def test_submission_after_deadline_is_blocked(self):
        self.client.login(username="STU01", password="pass")
        resp = self.client.get(f"/student/assignment/{self.assignment_past.id}/")
        self.assertNotContains(resp, "Add File")
        self.assertNotContains(resp, "Submit")
        self.assertContains(resp, "Deadline has passed")

    def test_cannot_post_after_deadline(self):
        self.client.login(username="STU01", password="pass")
        pdf = self._make_pdf()
        resp = self.client.post(
            f"/student/assignment/{self.assignment_past.id}/",
            {"file": pdf, "submit": "Submit"},
        )
        self.assertEqual(Submission.objects.count(), 0)
        self.assertContains(resp, "Deadline has passed")

    # --- File constraints ---
    def test_reject_invalid_file_extension(self):
        with self.assertRaises(ValidationError):
            validate_file_extension(SimpleUploadedFile("test.exe", b"data", content_type="application/x-msdownload"))

    def test_reject_oversized_file(self):
        big = SimpleUploadedFile("test.pdf", b"a" * (5 * 1024 * 1024 + 1), content_type="application/pdf")
        with self.assertRaises(ValidationError):
            validate_file_size(big)

    def test_form_rejects_invalid_file(self):
        self.client.login(username="STU01", password="pass")
        exe = SimpleUploadedFile("bad.exe", b"data", content_type="application/x-msdownload")
        resp = self.client.post(
            f"/student/assignment/{self.assignment_bsstc.id}/",
            {"file": exe, "save": "Add File"},
        )
        self.assertContains(resp, "Unsupported file type")

    # --- Ownership ---
    def test_student_cannot_see_other_student_submission(self):
        self.client.login(username="STU01", password="pass")
        pdf = self._make_pdf()
        self.client.post(
            f"/student/assignment/{self.assignment_bsstc.id}/",
            {"file": pdf, "save": "Add File"},
        )
        # Try viewing as another student — the student can only see own assignment detail
        self.client.logout()
        self.client.login(username="STU02", password="pass")
        resp = self.client.get(f"/student/assignment/{self.assignment_bsstc.id}/")
        # STU02 is BNTC, so they get 404 because class isolation kicks in
        self.assertEqual(resp.status_code, 404)

    # --- One submission per student ---
    def test_reupload_updates_existing_submission(self):
        self.client.login(username="STU01", password="pass")
        pdf1 = self._make_pdf("v1.pdf")
        self.client.post(
            f"/student/assignment/{self.assignment_bsstc.id}/",
            {"file": pdf1, "save": "Add File"},
        )
        self.assertEqual(Submission.objects.count(), 1)
        pdf2 = self._make_pdf("v2.pdf")
        self.client.post(
            f"/student/assignment/{self.assignment_bsstc.id}/",
            {"file": pdf2, "submit": "Submit"},
        )
        self.assertEqual(Submission.objects.count(), 1)
        sub = Submission.objects.first()
        self.assertIsNotNone(sub.submitted_at)

    # --- Instructor ownership ---
    def test_instructor_see_only_own_offerings(self):
        other_user = User.objects.create_user(username="INST02", password="pass")
        other_inst = Instructor.objects.create(
            user=other_user, staff_id="INST02", full_name="Other Inst"
        )
        other_course = Course.objects.create(course_code="C999", title="Other Course")
        CourseOffering.objects.create(
            course=other_course, class_group=self.bsstc, instructor=other_inst
        )
        self.client.login(username="INST01", password="pass")
        resp = self.client.get("/instructor/dashboard/")
        self.assertContains(resp, "Course 1")
        self.assertNotContains(resp, "Other Course")

    def test_instructor_cannot_view_another_instructors_assignment(self):
        other_user = User.objects.create_user(username="INST03", password="pass")
        other_inst = Instructor.objects.create(
            user=other_user, staff_id="INST03", full_name="Other Inst"
        )
        other_course = Course.objects.create(course_code="C777", title="Secret")
        other_offering = CourseOffering.objects.create(
            course=other_course, class_group=self.bsstc, instructor=other_inst
        )
        secret_assign = Assignment.objects.create(
            course_offering=other_offering,
            title="Secret Assignment",
            question="shh",
            deadline=self.future_deadline,
        )
        self.client.login(username="INST01", password="pass")
        resp = self.client.get(f"/instructor/assignment/{secret_assign.id}/")
        self.assertEqual(resp.status_code, 404)
