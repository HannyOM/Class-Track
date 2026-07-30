from django.urls import path

from assignments import views

urlpatterns = [
    path("instructor/course/<int:offering_id>/assignment/create/", views.instructor_assignment_create, name="instructor_assignment_create"),
]
