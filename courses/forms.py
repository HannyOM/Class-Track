from django import forms

from courses.models import ClassGroup, Course, CourseOffering


class CourseCreateForm(forms.ModelForm):
    class_group = forms.ModelMultipleChoiceField(
        queryset=ClassGroup.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        help_text="Select one or both cohorts.",
    )

    class Meta:
        model = Course
        fields = ["course_code", "title", "description"]

    def __init__(self, *args, **kwargs):
        self.instructor = kwargs.pop("instructor", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        course = super().save(commit=commit)
        if commit:
            for group in self.cleaned_data["class_group"]:
                CourseOffering.objects.create(
                    course=course,
                    class_group=group,
                    instructor=self.instructor,
                )
        return course
