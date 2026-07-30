from django.contrib.auth.models import User
from django.db import models


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    student_id = models.CharField(max_length=20, unique=True)
    class_group = models.ForeignKey("courses.ClassGroup", on_delete=models.PROTECT, related_name="students")
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.student_id})"


class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="instructor_profile")
    staff_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.staff_id})"
