from rest_framework import serializers
from .models import User
from jobs.serializers import JobSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "user_id",
            "fcm_token",
            "username",
            "email",
            "phone_number",
            "address",
            "profile_picture",
            "user_type",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["user_id", "date_joined", "last_login", "fcm_token"]

    def validate_phone_number(self, value):
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        if not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain digits only. Remove any spaces, dashes, or special characters."
            )
        if len(value) != 10:
            raise serializers.ValidationError(
                f"Phone number must be exactly 10 digits long. You entered {len(value)} digit(s)."
            )
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "This phone number is already registered to another account. Please use a different number."
            )
        return value

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email address is required.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "An account with this email address already exists. Please log in or use a different email."
            )
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.phone_number = validated_data.get(
            "phone_number", instance.phone_number
        )
        instance.address = validated_data.get("address", instance.address)
        instance.profile_picture = validated_data.get(
            "profile_picture", instance.profile_picture
        )
        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            "required": "Password is required.",
            "blank": "Password cannot be blank.",
            "min_length": "Password must be at least 8 characters long.",
        },
    )
    password2 = serializers.CharField(
        write_only=True,
        error_messages={
            "required": "Please confirm your password.",
            "blank": "Password confirmation cannot be blank.",
        },
    )

    class Meta:
        model = User
        fields = [
            "user_id",
            "username",
            "email",
            "phone_number",
            "address",
            "profile_picture",
            "user_type",
            "date_joined",
            "last_login",
            "password",
            "password2",
        ]
        read_only_fields = ["user_id", "date_joined", "last_login"]
        extra_kwargs = {
            "email": {
                "error_messages": {
                    "required": "Email address is required.",
                    "blank": "Email address cannot be blank.",
                    "invalid": "Please enter a valid email address (e.g. you@example.com).",
                }
            },
            "phone_number": {
                "error_messages": {
                    "required": "Phone number is required.",
                    "blank": "Phone number cannot be blank.",
                }
            },
            "user_type": {
                "error_messages": {
                    "invalid_choice": "Invalid user type. Choose from: admin, technician, driver, or inspector.",
                }
            },
        }

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email address is required.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "An account with this email address already exists. Please log in or use a different email."
            )
        return value

    def validate_phone_number(self, value):
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        if not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain digits only. Remove any spaces, dashes, or special characters."
            )
        if len(value) != 10:
            raise serializers.ValidationError(
                f"Phone number must be exactly 10 digits long. You entered {len(value)} digit(s)."
            )
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "This phone number is already registered to another account. Please use a different number."
            )
        return value

    def validate_address(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Address is required.")
        return value

    def validate(self, attrs):
        password = attrs.get("password", "")
        password2 = attrs.get("password2", "")

        if not password2:
            raise serializers.ValidationError(
                {"password2": "Please confirm your password."}
            )
        if password != password2:
            raise serializers.ValidationError(
                {"password2": "Passwords do not match. Please make sure both fields are identical."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "phone_number",
            "address",
            "profile_picture",
        ]
        read_only_fields = ["user_id", "date_joined", "last_login"]
        extra_kwargs = {
            "email": {
                "error_messages": {
                    "invalid": "Please enter a valid email address (e.g. you@example.com).",
                }
            },
        }

    def validate_phone_number(self, value):
        if not value:
            raise serializers.ValidationError("Phone number cannot be blank.")
        if not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain digits only. Remove any spaces, dashes, or special characters."
            )
        if len(value) != 10:
            raise serializers.ValidationError(
                f"Phone number must be exactly 10 digits long. You entered {len(value)} digit(s)."
            )
        # Exclude the current user's own number from the uniqueness check
        qs = User.objects.filter(phone_number=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "This phone number is already registered to another account. Please use a different number."
            )
        return value

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email address cannot be blank.")
        # Exclude the current user's own email from the uniqueness check
        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "This email address is already registered to another account. Please use a different email."
            )
        return value

    def validate_profile_picture(self, value):
        if value and not (value.startswith("http://") or value.startswith("https://")):
            raise serializers.ValidationError(
                "Profile picture must be a valid URL starting with http:// or https://."
            )
        return value

    def update(self, instance, validated_data):
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.phone_number = validated_data.get(
            "phone_number", instance.phone_number
        )
        instance.address = validated_data.get("address", instance.address)
        instance.profile_picture = validated_data.get(
            "profile_picture", instance.profile_picture
        )
        instance.save()
        return instance


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            "required": "Email address is required.",
            "blank": "Email address cannot be blank.",
            "invalid": "Please enter a valid email address (e.g. you@example.com).",
        }
    )
    password = serializers.CharField(
        write_only=True,
        error_messages={
            "required": "Password is required.",
            "blank": "Password cannot be blank.",
        },
    )

    def validate(self, attrs):
        email = attrs.get("email", "").strip()
        password = attrs.get("password", "")

        if not email:
            raise serializers.ValidationError(
                {"email": "Email address is required to log in."}
            )
        if not password:
            raise serializers.ValidationError(
                {"password": "Password is required to log in."}
            )

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError(
                {
                    "email": (
                        "No account found with this email address. "
                        "Please check your email or create a new account."
                    )
                }
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {
                    "email": (
                        "This account has been deactivated. "
                        "Please contact support to restore access."
                    )
                }
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                {
                    "password": (
                        "Incorrect password. "
                        "Please double-check your password and try again."
                    )
                }
            )

        attrs["user"] = user
        return attrs


class UserFetchAssignedJobsSerializer(serializers.ModelSerializer):
    assigned_jobs = JobSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["assigned_jobs"]


class UpdateFCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["fcm_token"]
        extra_kwargs = {
            "fcm_token": {
                "required": True,
                "allow_blank": False,
                "error_messages": {
                    "required": "A push notification token (FCM token) is required.",
                    "blank": "Push notification token cannot be blank.",
                },
            }
        }

    def validate_fcm_token(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "A valid push notification token is required to enable notifications."
            )
        return value
