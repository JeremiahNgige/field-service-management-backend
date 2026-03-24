from django.urls import path
from .views import (
    JobCreateView,
    JobListView,
    JobUpdateView,
    JobDeleteView,
    JobDetailView,
    JobAssignView,
)

urlpatterns = [
    path("create/", JobCreateView.as_view(), name="create"),
    path("list/", JobListView.as_view(), name="list"),
    path("update/<uuid:job_id>/", JobUpdateView.as_view(), name="update"),
    path("delete/<uuid:job_id>/", JobDeleteView.as_view(), name="delete"),
    path("detail/<uuid:job_id>/", JobDetailView.as_view(), name="detail"),
    path("assign/<uuid:job_id>/", JobAssignView.as_view(), name="assign"),
]

app_name = "jobs"
