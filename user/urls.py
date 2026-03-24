from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserUpdateView,
    UserLogoutView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("update/", UserUpdateView.as_view(), name="update"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
]

app_name = "user"
