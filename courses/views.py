from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from courses.forms import CourseCreateForm


@login_required
def instructor_course_list(request):
    instructor = request.user.instructor_profile
    offerings = instructor.offerings.select_related("course", "class_group").all()
    return render(request, "instructor/course_list.html", {
        "instructor": instructor,
        "offerings": offerings,
    })


@login_required
def instructor_course_create(request):
    instructor = request.user.instructor_profile
    if request.method == "POST":
        form = CourseCreateForm(request.POST, instructor=instructor)
        if form.is_valid():
            form.save()
            return redirect("instructor_dashboard")
    else:
        form = CourseCreateForm(instructor=instructor)
    return render(request, "instructor/course_form.html", {
        "instructor": instructor,
        "form": form,
    })
