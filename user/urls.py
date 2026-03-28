from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserUpdateView,
    UserLogoutView,
    UserFetchAssignedJobsView,
    UserProfileView,
    UserUpdateFCMTokenView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("update/", UserUpdateView.as_view(), name="update"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path(
        "fetch-assigned-jobs/",
        UserFetchAssignedJobsView.as_view(),
        name="fetch-assigned-jobs",
    ),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("update-fcm-token/", UserUpdateFCMTokenView.as_view(), name="update-fcm-token"),
]

app_name = "user"
