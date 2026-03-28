from django.urls import path
from .views import (
    JobCreateView,
    JobListView,
    JobUpdateView,
    JobDeleteView,
    JobDetailView,
    GenerateUploadURLsView,
    GetDownloadURLsView,
)

urlpatterns = [
    path("create/", JobCreateView.as_view(), name="create"),
    path("list/", JobListView.as_view(), name="list"),
    path("update/<uuid:job_id>/", JobUpdateView.as_view(), name="update"),
    path("delete/<uuid:job_id>/", JobDeleteView.as_view(), name="delete"),
    path("detail/<uuid:job_id>/", JobDetailView.as_view(), name="detail"),
    path("upload-urls/", GenerateUploadURLsView.as_view(), name="upload-urls"),
    path("download-urls/", GetDownloadURLsView.as_view(), name="download-urls"),
]

app_name = "jobs"
