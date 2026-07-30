from django.db import models

from assignments.validators import validate_file_extension, validate_file_size


def submission_upload_path(instance, filename: str) -> str:
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    return f"submissions/assignment_{instance.assignment_id}_student_{instance.student_id}.{ext}"


class Assignment(models.Model):
    course_offering = models.ForeignKey(
        "courses.CourseOffering", on_delete=models.CASCADE, related_name="assignments"
    )
    title = models.CharField(max_length=255)
    question = models.TextField()
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-deadline"]

    def __str__(self) -> str:
        return f"{self.title} ({self.course_offering.course.course_code})"


class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        "accounts.Student", on_delete=models.CASCADE, related_name="submissions"
    )
    file = models.FileField(
        upload_to=submission_upload_path,
        validators=[validate_file_extension, validate_file_size],
    )
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("assignment", "student")
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"{self.student.full_name} — {self.assignment.title}"
