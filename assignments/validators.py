import os

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            _("Unsupported file type '%(ext)s'. Only PDF, DOC, and DOCX files are allowed."),
            params={"ext": ext},
        )


def validate_file_size(value):
    if value.size > MAX_FILE_SIZE:
        raise ValidationError(
            _("File size must be no more than 5 MB. Your file is %(size)s MB."),
            params={"size": round(value.size / (1024 * 1024), 2)},
        )
