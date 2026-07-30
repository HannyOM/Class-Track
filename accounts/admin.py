from django.contrib import admin

from accounts.models import Instructor, Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["student_id", "full_name", "class_group", "email"]
    search_fields = ["student_id", "full_name"]


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ["staff_id", "full_name", "email"]
    search_fields = ["staff_id", "full_name"]
