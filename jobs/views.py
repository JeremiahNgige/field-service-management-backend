from django.conf import settings
from django.http import Http404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
    PermissionDenied,
    NotAuthenticated,
    MethodNotAllowed,
    UnsupportedMediaType,
    Throttled,
)
from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
    FieldError,
)
from django.db import IntegrityError, DatabaseError, OperationalError
from .models import Job
from .serializers import JobSerializer
from rest_framework.pagination import CursorPagination
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
import uuid


def _get_error_message(e):
    """
    Extract the first human-readable error message from a DRF ValidationError.
    Returns a plain string suitable for displaying in a mobile UI.
    """
    error_detail = e.detail
    if isinstance(error_detail, dict):
        if "non_field_errors" in error_detail:
            msg = error_detail["non_field_errors"][0]
        else:
            first_key = next(iter(error_detail))
            value = error_detail[first_key]
            msg = value[0] if isinstance(value, list) else value
    elif isinstance(error_detail, list):
        msg = error_detail[0]
    else:
        msg = error_detail
    # DRF ErrorDetail objects are string-compatible; convert to plain str
    return str(msg)


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


# ---------------------------------------------------------------------------
# Job Views
# ---------------------------------------------------------------------------


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

        except DRFValidationError as e:
            return Response(
                {
                    "message": _get_error_message(e),
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError as e:
            error_str = str(e).lower()
            if "unique" in error_str:
                message = (
                    "A job with these details already exists. "
                    "Please check for duplicate entries."
                )
            elif "foreign key" in error_str or "not present in table" in error_str:
                message = (
                    "The assigned user does not exist. "
                    "Please assign the job to a valid user."
                )
            else:
                message = (
                    "A database conflict occurred while creating the job. "
                    "Please verify your data and try again."
                )
            return Response({"message": message}, status=status.HTTP_409_CONFLICT)

        except OperationalError:
            return Response(
                {
                    "message": (
                        "The database is temporarily unavailable. "
                        "Please try again in a moment."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DatabaseError:
            return Response(
                {
                    "message": (
                        "An unexpected database error occurred while creating the job. "
                        "Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred while creating the job. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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

        except DRFValidationError as e:
            return Response(
                {
                    "message": _get_error_message(e),
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except FieldError:
            return Response(
                {
                    "message": (
                        "An invalid filter or ordering parameter was provided. "
                        "Please check your query parameters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except OperationalError:
            return Response(
                {
                    "message": (
                        "The database is temporarily unavailable. "
                        "Please try again in a moment."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DatabaseError:
            return Response(
                {
                    "message": (
                        "An unexpected database error occurred while fetching jobs. "
                        "Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred while fetching the job list. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class JobUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer
    lookup_field = "job_id"
    queryset = Job.objects.all()

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

        except Http404:
            return Response(
                {
                    "message": (
                        "The job you are trying to update does not exist. "
                        "It may have been deleted."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except DRFValidationError as e:
            return Response(
                {
                    "message": _get_error_message(e),
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied:
            return Response(
                {
                    "message": (
                        "You do not have permission to update this job."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except IntegrityError as e:
            error_str = str(e).lower()
            if "foreign key" in error_str or "not present in table" in error_str:
                message = (
                    "The assigned user does not exist. "
                    "Please assign the job to a valid user."
                )
            else:
                message = (
                    "A database conflict occurred while updating the job. "
                    "Please verify your data and try again."
                )
            return Response({"message": message}, status=status.HTTP_409_CONFLICT)

        except OperationalError:
            return Response(
                {
                    "message": (
                        "The database is temporarily unavailable. "
                        "Please try again in a moment."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DatabaseError:
            return Response(
                {
                    "message": (
                        "An unexpected database error occurred while updating the job. "
                        "Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred while updating the job. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class JobDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer
    lookup_field = "job_id"
    queryset = Job.objects.all()

    def delete(self, request, *args, **kwargs):
        try:
            job = self.get_object()
            job.delete()
            return Response(
                {"message": "Job deleted successfully"},
                status=status.HTTP_200_OK,
            )

        except Http404:
            return Response(
                {
                    "message": (
                        "The job you are trying to delete does not exist. "
                        "It may have already been removed."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except DRFValidationError as e:
            return Response(
                {
                    "message": _get_error_message(e),
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied:
            return Response(
                {
                    "message": "You do not have permission to delete this job."
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except ProtectedError:
            return Response(
                {
                    "message": (
                        "This job cannot be deleted because it is linked to other records. "
                        "Please remove associated data first."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        except OperationalError:
            return Response(
                {
                    "message": (
                        "The database is temporarily unavailable. "
                        "Please try again in a moment."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DatabaseError:
            return Response(
                {
                    "message": (
                        "An unexpected database error occurred while deleting the job. "
                        "Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred while deleting the job. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class JobDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer
    lookup_field = "job_id"
    queryset = Job.objects.all()

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

        except Http404:
            return Response(
                {
                    "message": (
                        "The requested job could not be found. "
                        "It may have been deleted or the ID is incorrect."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except DRFValidationError as e:
            return Response(
                {
                    "message": _get_error_message(e),
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied:
            return Response(
                {
                    "message": "You do not have permission to view this job."
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except OperationalError:
            return Response(
                {
                    "message": (
                        "The database is temporarily unavailable. "
                        "Please try again in a moment."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DatabaseError:
            return Response(
                {
                    "message": (
                        "An unexpected database error occurred while fetching the job. "
                        "Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred while fetching the job. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------------------
# S3 / MinIO Upload & Download URL Views
# ---------------------------------------------------------------------------


def _get_s3_client():
    """Return a configured boto3 S3 client pointing at MinIO."""
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=getattr(settings, "AWS_S3_REGION_NAME", "us-east-1"),
        use_ssl=getattr(settings, "AWS_S3_USE_SSL", False),
    )


class GenerateUploadURLsView(APIView):
    """
    Generates presigned PUT URLs so the Flutter client can upload
    files (signature + photos) directly to MinIO/S3 without routing
    large payloads through Django.

    Request body (JSON):
        {
            "image_count": 3,       # number of job photos to upload
            "has_signature": true   # whether a signature image is included
        }

    Response:
        {
            "signature": {
                "upload_url": "<presigned PUT URL>",
                "key": "signatures/<uuid>.png"
            },
            "images": [
                { "upload_url": "...", "key": "job-images/<uuid>.jpg" },
                ...
            ]
        }

    Flutter flow:
        1. Call this endpoint to get presigned URLs.
        2. PUT each file directly to its upload_url.
        3. POST the key values to the job update endpoint.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Guard: S3 storage must be configured
        if not getattr(settings, "USE_S3", False):
            return Response(
                {
                    "message": (
                        "File storage is not available on this server. "
                        "Please contact your administrator."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Validate image_count
        raw_count = request.data.get("image_count", 0)
        try:
            image_count = int(raw_count)
        except (TypeError, ValueError):
            return Response(
                {
                    "message": (
                        "'image_count' must be a whole number (e.g. 0, 1, 2). "
                        f"Received: {raw_count!r}"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if image_count < 0:
            return Response(
                {"message": "'image_count' cannot be negative."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if image_count > 20:
            return Response(
                {
                    "message": (
                        "You can upload at most 20 photos per request. "
                        f"You requested {image_count}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        has_signature = request.data.get("has_signature", False)

        if image_count == 0 and not has_signature:
            return Response(
                {
                    "message": (
                        "Nothing to upload. "
                        "Provide at least one photo or set 'has_signature' to true."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            s3 = _get_s3_client()
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            response = {"signature": None, "images": []}

            # Generate presigned URL for signature
            if has_signature:
                key = f"signatures/{uuid.uuid4()}.png"
                upload_url = s3.generate_presigned_url(
                    "put_object",
                    Params={"Bucket": bucket, "Key": key, "ContentType": "image/png"},
                    ExpiresIn=300,  # 5 minutes
                )
                response["signature"] = {"upload_url": upload_url, "key": key}

            # Generate presigned URLs for each photo
            for _ in range(image_count):
                key = f"job-images/{uuid.uuid4()}.jpg"
                upload_url = s3.generate_presigned_url(
                    "put_object",
                    Params={"Bucket": bucket, "Key": key, "ContentType": "image/jpeg"},
                    ExpiresIn=300,  # 5 minutes
                )
                response["images"].append({"upload_url": upload_url, "key": key})

            return Response(response, status=status.HTTP_200_OK)

        except NoCredentialsError:
            return Response(
                {
                    "message": (
                        "The server's file storage credentials are not configured. "
                        "Please contact your administrator."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except EndpointConnectionError:
            return Response(
                {
                    "message": (
                        "Unable to connect to the file storage server. "
                        "Please check your network or try again later."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchBucket":
                message = (
                    "The file storage bucket does not exist. "
                    "Please contact your administrator."
                )
            elif error_code == "AccessDenied":
                message = (
                    "Access to file storage was denied. "
                    "Please contact your administrator."
                )
            else:
                message = (
                    "The file storage service returned an error. "
                    "Please try again later."
                )
            return Response(
                {"message": message},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except DRFValidationError as e:
            return Response(
                {
                    "message": _get_error_message(e),
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred while generating upload URLs. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetDownloadURLsView(APIView):
    """
    Generates presigned GET URLs for one or more private MinIO object keys.

    The Flutter client calls this endpoint whenever it needs to display an image.
    Django generates a short-lived URL and returns it — the bucket itself remains
    private and is never directly accessible from the internet.

    Request body (JSON):
        {
            "keys": ["signatures/abc.png", "job-images/img1.jpg"]
        }

    Response:
        {
            "urls": {
                "signatures/abc.png":    "http://minio:9000/...?X-Amz-Signature=...",
                "job-images/img1.jpg":   "http://minio:9000/...?X-Amz-Signature=..."
            }
        }

    Flutter usage:
        // After fetching a job, pass the stored keys to this endpoint:
        final res = await api.post('/api/jobs/download-urls/', body: {
          "keys": [job.signature, ...job.photos]
        });
        final signatureUrl = res['urls'][job.signature];

    Notes:
        - Each URL expires in 30 minutes (DOWNLOAD_URL_EXPIRY setting or default).
        - At most 50 keys can be resolved per request.
        - Null / empty keys in the list are silently ignored.
    """

    permission_classes = [IsAuthenticated]

    EXPIRY_SECONDS = getattr(settings, "DOWNLOAD_URL_EXPIRY", 1800)  # 30 min default
    MAX_KEYS = 50

    def post(self, request):
        # Guard: S3 storage must be configured
        if not getattr(settings, "USE_S3", False):
            return Response(
                {
                    "message": (
                        "File storage is not available on this server. "
                        "Please contact your administrator."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        keys = request.data.get("keys", [])

        if not isinstance(keys, list):
            return Response(
                {
                    "message": (
                        "'keys' must be a list of file path strings. "
                        f"Received type: {type(keys).__name__!r}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filter out nulls/empty strings
        keys = [k for k in keys if k]

        if len(keys) > self.MAX_KEYS:
            return Response(
                {
                    "message": (
                        f"Too many keys requested. You can resolve at most {self.MAX_KEYS} "
                        f"file keys per request. You provided {len(keys)}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not keys:
            return Response({"urls": {}}, status=status.HTTP_200_OK)

        # Validate that all keys are non-empty strings
        invalid_keys = [k for k in keys if not isinstance(k, str) or not k.strip()]
        if invalid_keys:
            return Response(
                {
                    "message": (
                        "All keys must be non-empty strings. "
                        "Please remove any blank or non-string entries."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            s3 = _get_s3_client()
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            urls = {}

            for key in keys:
                urls[key] = s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=self.EXPIRY_SECONDS,
                )

            return Response({"urls": urls}, status=status.HTTP_200_OK)

        except NoCredentialsError:
            return Response(
                {
                    "message": (
                        "The server's file storage credentials are not configured. "
                        "Please contact your administrator."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except EndpointConnectionError:
            return Response(
                {
                    "message": (
                        "Unable to connect to the file storage server. "
                        "Please check your network or try again later."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                message = (
                    "One or more of the requested files could not be found in storage. "
                    "The file may have been deleted or the key is incorrect."
                )
            elif error_code == "NoSuchBucket":
                message = (
                    "The file storage bucket does not exist. "
                    "Please contact your administrator."
                )
            elif error_code == "AccessDenied":
                message = (
                    "Access to file storage was denied. "
                    "Please contact your administrator."
                )
            else:
                message = (
                    "The file storage service returned an error. "
                    "Please try again later."
                )
            return Response(
                {"message": message},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except DRFValidationError as e:
            return Response(
                {
                    "message": _get_error_message(e),
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred while generating download URLs. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------------------
# Import guard for ProtectedError (used in JobDeleteView)
# ---------------------------------------------------------------------------
from django.db.models import ProtectedError  # noqa: E402
