from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from assignments.forms_instructor import AssignmentCreateForm


@login_required
def instructor_assignment_create(request, offering_id):
    instructor = request.user.instructor_profile
    offering = instructor.offerings.filter(id=offering_id).first()

    if request.method == "POST":
        form = AssignmentCreateForm(request.POST, instructor=instructor)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.course_offering = offering
            assignment.save()
            return redirect("instructor_course_detail", offering_id=offering_id)
    else:
        form = AssignmentCreateForm(instructor=instructor)
        if offering:
            form.fields["course_offering"].initial = offering
            form.fields["course_offering"].queryset = instructor.offerings.filter(id=offering_id)
    return render(request, "instructor/assignment_form.html", {
        "instructor": instructor,
        "form": form,
        "offering": offering,
    })
