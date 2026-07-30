from django.contrib import admin

from assignments.models import Assignment, Submission


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["title", "course_offering", "deadline", "created_at"]
    list_filter = ["course_offering__class_group"]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["assignment", "student", "submitted_at"]
    list_filter = ["assignment"]
