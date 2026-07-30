from django.contrib.auth.views import LoginView


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_redirect_url(self):
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, "student_profile"):
                return "/student/dashboard/"
            if hasattr(self.request.user, "instructor_profile"):
                return "/instructor/dashboard/"
        return "/login/"
