from django.db import models


class ClassGroup(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "class groups"

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class Course(models.Model):
    course_code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.course_code} — {self.title}"


class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="offerings")
    class_group = models.ForeignKey(ClassGroup, on_delete=models.PROTECT, related_name="offerings")
    instructor = models.ForeignKey(
        "accounts.Instructor", on_delete=models.PROTECT, related_name="offerings"
    )

    class Meta:
        unique_together = ("course", "class_group")
        verbose_name_plural = "course offerings"

    def __str__(self) -> str:
        return f"{self.course.title} — {self.class_group.code} ({self.instructor.full_name})"
