from django import forms

from assignments.models import Assignment


class AssignmentCreateForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["course_offering", "title", "question", "deadline"]
        widgets = {
            "deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "question": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        instructor = kwargs.pop("instructor", None)
        super().__init__(*args, **kwargs)
        if instructor:
            self.fields["course_offering"].queryset = instructor.offerings.select_related(
                "course", "class_group"
            )
