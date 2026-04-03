from django.db import IntegrityError, DatabaseError, OperationalError
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
    Throttled,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import (
    TokenError,
    InvalidToken,
)

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserUpdateSerializer,
    UserSerializer,
    UpdateFCMTokenSerializer,
)
from .throttles import LoginRateThrottle

from jobs.models import Job
from jobs.serializers import JobSerializer
from jobs.views import JobCursorPagination


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
    return str(msg)


# ---------------------------------------------------------------------------
# Auth Views
# ---------------------------------------------------------------------------


class UserRegistrationView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {
                    "message": "Account created successfully. You can now log in.",
                    "user": serializer.data,
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
            if "email" in error_str:
                message = (
                    "An account with this email address already exists. "
                    "Please log in or use a different email."
                )
            elif "phone" in error_str:
                message = (
                    "This phone number is already registered to another account. "
                    "Please use a different phone number."
                )
            elif "username" in error_str:
                message = (
                    "This username is already taken. "
                    "Please choose a different username."
                )
            else:
                message = (
                    "An account conflict occurred. "
                    "The email or phone number may already be in use."
                )
            return Response({"message": message}, status=status.HTTP_409_CONFLICT)

        except OperationalError:
            return Response(
                {
                    "message": (
                        "The server is temporarily unavailable. "
                        "Please try registering again in a moment."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DatabaseError:
            return Response(
                {
                    "message": (
                        "A database error occurred while creating your account. "
                        "Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred during registration. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]
    serializer_class = UserLoginSerializer

    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Logged in successfully.",
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )

        except DRFValidationError as e:
            return Response(
                {"message": _get_error_message(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Throttled as e:
            wait = e.wait
            wait_msg = (
                f" Please wait {int(wait)} seconds before trying again." if wait else ""
            )
            return Response(
                {
                    "message": (
                        "Too many login attempts. Your account has been temporarily locked."
                        + wait_msg
                    )
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except OperationalError:
            return Response(
                {
                    "message": (
                        "The server is temporarily unavailable. "
                        "Please try logging in again in a moment."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred during login. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer

    def put(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {
                    "message": "Profile updated successfully.",
                    "user": serializer.data,
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
        except IntegrityError as e:
            error_str = str(e).lower()
            if "email" in error_str:
                message = (
                    "This email address is already registered to another account. "
                    "Please use a different email."
                )
            elif "phone" in error_str:
                message = (
                    "This phone number is already registered to another account. "
                    "Please use a different phone number."
                )
            else:
                message = (
                    "A conflict occurred while updating your profile. "
                    "Some of the details you provided may already be in use."
                )
            return Response({"message": message}, status=status.HTTP_409_CONFLICT)

        except OperationalError:
            return Response(
                {
                    "message": (
                        "The server is temporarily unavailable. "
                        "Please try updating your profile again in a moment."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DatabaseError:
            return Response(
                {
                    "message": (
                        "A database error occurred while saving your profile. "
                        "Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred while updating your profile. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserProfileView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        try:
            user = request.user
            serializer = self.get_serializer(user)
            return Response(
                {
                    "message": "Profile fetched successfully.",
                    "user": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except OperationalError:
            return Response(
                {
                    "message": (
                        "The server is temporarily unavailable. "
                        "Please try fetching your profile again in a moment."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DatabaseError:
            return Response(
                {
                    "message": (
                        "A database error occurred while fetching your profile. "
                        "Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred while fetching your profile. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserLogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                # Blacklist the refresh token to fully invalidate the session
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except TokenError:
                    # Token is already invalid or expired — logout is still successful
                    pass
            return Response(
                {"message": "Logged out successfully."},
                status=status.HTTP_205_RESET_CONTENT,
            )

        except InvalidToken:
            # Even with an invalid token, clear the session on the client
            return Response(
                {
                    "message": (
                        "Your session token is invalid or has already expired. "
                        "You have been logged out."
                    )
                },
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred during logout. Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserFetchAssignedJobsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer
    pagination_class = JobCursorPagination

    def get_queryset(self):
        return Job.objects.filter(assigned_to=self.request.user)

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
                    "message": "Your assigned jobs were fetched successfully.",
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
        except OperationalError:
            return Response(
                {
                    "message": (
                        "The server is temporarily unavailable. "
                        "Please try fetching your jobs again in a moment."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DatabaseError:
            return Response(
                {
                    "message": (
                        "A database error occurred while fetching your assigned jobs. "
                        "Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred while fetching your assigned jobs. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserUpdateFCMTokenView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateFCMTokenSerializer

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {
                    "message": "Push notification token updated successfully.",
                    "fcm_token": user.fcm_token,
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
        except OperationalError:
            return Response(
                {
                    "message": (
                        "The server is temporarily unavailable. "
                        "Please try updating your notification token again in a moment."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DatabaseError:
            return Response(
                {
                    "message": (
                        "A database error occurred while updating your push notification token. "
                        "Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return Response(
                {
                    "message": (
                        "An unexpected error occurred while updating your push notification token. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
