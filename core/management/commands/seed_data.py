from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Instructor, Student
from assignments.models import Assignment
from courses.models import ClassGroup, Course, CourseOffering


class Command(BaseCommand):
    help = "Seed the database with demo data."

    def handle(self, *args, **options):
        bsstc, _ = ClassGroup.objects.get_or_create(code="BSSTC", name="Basic Space Science and Technology Course")
        bntc, _ = ClassGroup.objects.get_or_create(code="BNTC", name="Basic Non-Technical Course")

        # Instructors
        user_i1, _ = User.objects.get_or_create(username="INST001")
        user_i1.set_password("password")
        user_i1.save()
        inst1, _ = Instructor.objects.get_or_create(
            user=user_i1, staff_id="INST001", full_name="Dr. Ada Lovelace"
        )

        user_i2, _ = User.objects.get_or_create(username="INST002")
        user_i2.set_password("password")
        user_i2.save()
        inst2, _ = Instructor.objects.get_or_create(
            user=user_i2, staff_id="INST002", full_name="Prof. Alan Turing"
        )

        # Courses
        course1, _ = Course.objects.get_or_create(
            course_code="MATH101", title="Mathematics for Space Applications",
            description="Foundational mathematics for space science."
        )
        course2, _ = Course.objects.get_or_create(
            course_code="PHY101", title="Introduction to Physics",
            description="Core physics concepts."
        )
        course3, _ = Course.objects.get_or_create(
            course_code="COM101", title="Communication Skills (Combined)",
            description="Combined course for both cohorts."
        )

        # Offerings
        CourseOffering.objects.get_or_create(course=course1, class_group=bsstc, instructor=inst1)
        CourseOffering.objects.get_or_create(course=course2, class_group=bsstc, instructor=inst1)
        CourseOffering.objects.get_or_create(course=course2, class_group=bntc, instructor=inst2)
        off_bsstc, _ = CourseOffering.objects.get_or_create(course=course3, class_group=bsstc, instructor=inst1)
        off_bntc, _ = CourseOffering.objects.get_or_create(course=course3, class_group=bntc, instructor=inst2)

        # Students
        user_s1, _ = User.objects.get_or_create(username="STU001")
        user_s1.set_password("password")
        user_s1.save()
        Student.objects.get_or_create(
            user=user_s1, student_id="STU001", class_group=bsstc, full_name="Alice Johnson"
        )

        user_s2, _ = User.objects.get_or_create(username="STU002")
        user_s2.set_password("password")
        user_s2.save()
        Student.objects.get_or_create(
            user=user_s2, student_id="STU002", class_group=bsstc, full_name="Bob Smith"
        )

        user_s3, _ = User.objects.get_or_create(username="STU003")
        user_s3.set_password("password")
        user_s3.save()
        Student.objects.get_or_create(
            user=user_s3, student_id="STU003", class_group=bntc, full_name="Carol Williams"
        )

        # Assignments
        deadline_future = timezone.now() + timezone.timedelta(days=7)
        deadline_past = timezone.now() - timezone.timedelta(days=1)

        Assignment.objects.get_or_create(
            course_offering=off_bsstc, title="Homework 1: Vectors",
            question="Solve the vector problems from chapter 1.", deadline=deadline_future
        )
        Assignment.objects.get_or_create(
            course_offering=off_bsstc, title="Homework 2: Matrices",
            question="Practice matrix operations.", deadline=deadline_past
        )
        Assignment.objects.get_or_create(
            course_offering=off_bntc, title="Essay: Communication Theory",
            question="Write a 500-word essay on communication models.", deadline=deadline_future
        )

        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))
        self.stdout.write("Instructor login: INST001 / password")
        self.stdout.write("Student login: STU001 / password")
