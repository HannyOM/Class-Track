from django.urls import path

from dashboard import views

urlpatterns = [
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/assignment/<int:assignment_id>/", views.student_assignment_detail, name="student_assignment_detail"),
    path("instructor/dashboard/", views.instructor_dashboard, name="instructor_dashboard"),
    path("instructor/course/<int:offering_id>/", views.instructor_course_detail, name="instructor_course_detail"),
    path("instructor/assignment/<int:assignment_id>/", views.instructor_assignment_detail, name="instructor_assignment_detail"),
]
