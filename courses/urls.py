from django.urls import path

from courses import views

urlpatterns = [
    path("instructor/courses/", views.instructor_course_list, name="instructor_course_list"),
    path("instructor/course/create/", views.instructor_course_create, name="instructor_course_create"),
]
