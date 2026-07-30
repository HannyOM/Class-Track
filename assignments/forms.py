from django import forms

from assignments.models import Submission
from assignments.validators import validate_file_extension, validate_file_size


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["file"]
        widgets = {
            "file": forms.FileInput(attrs={"accept": ".pdf,.doc,.docx"}),
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            validate_file_extension(file)
            validate_file_size(file)
        return file
