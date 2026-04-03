from django.contrib import admin
from django.urls import path, include

# ---------------------------------------------------------------------------
# API v1 routes
# To introduce v2 with breaking changes, add a second include block below
# and keep v1 intact for backwards compatibility.
# ---------------------------------------------------------------------------
v1_patterns = [
    path("user/", include("user.urls")),
    path("jobs/", include("jobs.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((v1_patterns, "v1"))),
]
