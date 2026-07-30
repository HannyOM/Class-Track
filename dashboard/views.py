from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from assignments.forms import SubmissionForm
from assignments.models import Assignment, Submission
from courses.models import CourseOffering


@login_required
def student_dashboard(request):
    student = request.user.student_profile
    class_group = student.class_group
    offerings = CourseOffering.objects.filter(class_group=class_group).prefetch_related(
        "assignments__submissions"
    ).select_related("course", "instructor")
    assignments_list = []
    for offering in offerings:
        for assignment in offering.assignments.all():
            submission = Submission.objects.filter(
                assignment=assignment, student=student
            ).first()
            assignments_list.append({
                "assignment": assignment,
                "course": offering.course,
                "submission": submission,
                "is_submitted": submission is not None and submission.submitted_at is not None,
                "deadline_passed": timezone.now() >= assignment.deadline,
            })
    return render(request, "student/dashboard.html", {
        "student": student,
        "assignments": assignments_list,
    })


@login_required
def student_assignment_detail(request, assignment_id):
    student = request.user.student_profile
    assignment = get_object_or_404(
        Assignment.objects.select_related("course_offering__course", "course_offering__class_group"),
        id=assignment_id,
        course_offering__class_group=student.class_group,
    )
    submission = Submission.objects.filter(assignment=assignment, student=student).first()
    deadline_passed = timezone.now() >= assignment.deadline
    form = SubmissionForm(instance=submission) if not deadline_passed else None

    if request.method == "POST" and not deadline_passed:
        form = SubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.assignment = assignment
            sub.student = student
            if "submit" in request.POST:
                sub.submitted_at = timezone.now()
            sub.save()
            return render(request, "student/assignment_detail.html", {
                "student": student,
                "assignment": assignment,
                "submission": sub,
                "is_submitted": sub.submitted_at is not None,
                "deadline_passed": False,
                "form": SubmissionForm(instance=sub) if sub.submitted_at is None else None,
            })

    return render(request, "student/assignment_detail.html", {
        "student": student,
        "assignment": assignment,
        "submission": submission,
        "is_submitted": submission is not None and submission.submitted_at is not None,
        "deadline_passed": deadline_passed,
        "form": form,
    })


@login_required
def instructor_dashboard(request):
    instructor = request.user.instructor_profile
    offerings = instructor.offerings.select_related("course", "class_group").all()
    total_courses = offerings.count()
    total_assignments = sum(o.assignments.count() for o in offerings)
    recent_submissions = Submission.objects.filter(
        assignment__course_offering__in=offerings,
        submitted_at__isnull=False,
    ).select_related(
        "assignment", "student", "assignment__course_offering__course"
    ).order_by("-submitted_at")[:10]

    return render(request, "instructor/dashboard.html", {
        "instructor": instructor,
        "offerings": offerings,
        "total_courses": total_courses,
        "total_assignments": total_assignments,
        "recent_submissions": recent_submissions,
    })


@login_required
def instructor_course_detail(request, offering_id):
    instructor = request.user.instructor_profile
    offering = get_object_or_404(
        CourseOffering.objects.select_related("course", "class_group"),
        id=offering_id,
        instructor=instructor,
    )
    assignments = offering.assignments.all()
    return render(request, "instructor/course_detail.html", {
        "instructor": instructor,
        "offering": offering,
        "assignments": assignments,
    })


@login_required
def instructor_assignment_detail(request, assignment_id):
    instructor = request.user.instructor_profile
    assignment = get_object_or_404(
        Assignment.objects.select_related("course_offering__course", "course_offering__class_group"),
        id=assignment_id,
        course_offering__instructor=instructor,
    )
    offering = assignment.course_offering
    students_in_class = offering.class_group.students.select_related("user").all()
    submissions = {
        s.student_id: s
        for s in Submission.objects.filter(assignment=assignment).select_related("student")
    }
    submitted_students = []
    not_submitted_students = []
    for student in students_in_class:
        sub = submissions.get(student.id)
        if sub and sub.submitted_at:
            submitted_students.append({"student": student, "submission": sub})
        else:
            not_submitted_students.append({"student": student})
    return render(request, "instructor/assignment_detail.html", {
        "instructor": instructor,
        "assignment": assignment,
        "submitted_students": submitted_students,
        "not_submitted_students": not_submitted_students,
    })
