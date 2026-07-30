from django.contrib.auth.views import LogoutView
from django.urls import path

from accounts.views import CustomLoginView

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="/login/"), name="logout"),
]
