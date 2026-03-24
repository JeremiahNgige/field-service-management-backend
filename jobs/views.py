from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Job
from .serializers import JobSerializer
from rest_framework.pagination import CursorPagination


class JobCursorPagination(CursorPagination):
    page_size = 25
    ordering = "-created_at"

    def get_paginated_response(self, data):
        return Response(
            {
                "message": "Jobs fetched successfully",
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "jobs": data,
            }
        )


# Job Views
class JobCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {
                    "message": "Job created successfully",
                    "job": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"message": "Job creation failed", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class JobListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer
    pagination_class = JobCursorPagination
    queryset = Job.objects.all()

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(
                {
                    "message": "Jobs fetched successfully",
                    "jobs": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": "Jobs fetching failed", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class JobUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer
    lookup_field = "job_id"

    def put(self, request, *args, **kwargs):
        try:
            job = self.get_object()
            serializer = self.get_serializer(job, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {
                    "message": "Job updated successfully",
                    "job": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": "Job update failed", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class JobDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer
    lookup_field = "job_id"

    def delete(self, request, *args, **kwargs):
        try:
            job = self.get_object()
            job.delete()
            return Response(
                {
                    "message": "Job deleted successfully",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": "Job deletion failed", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class JobDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer
    lookup_field = "job_id"

    def get(self, request, *args, **kwargs):
        try:
            job = self.get_object()
            serializer = self.get_serializer(job)
            return Response(
                {
                    "message": "Job fetched successfully",
                    "job": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": "Job fetching failed", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
