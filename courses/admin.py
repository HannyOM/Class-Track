from django.contrib import admin

from courses.models import ClassGroup, Course, CourseOffering


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["course_code", "title"]
    search_fields = ["course_code", "title"]


@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ["course", "class_group", "instructor"]
    list_filter = ["class_group", "instructor"]
