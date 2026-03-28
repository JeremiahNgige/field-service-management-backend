from rest_framework import serializers
from .models import Job
from django.utils import timezone

VALID_STATUSES = ["unassigned", "assigned", "in_progress", "completed", "cancelled"]
VALID_PRIORITIES = ["low", "medium", "high"]
VALID_CURRENCIES = ["USD", "EUR", "GBP", "KES", "ZAR", "NGN", "GHS", "TZS", "UGX"]


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            "job_id",
            "title",
            "description",
            "status",
            "created_at",
            "updated_at",
            "assigned_to",
            "price",
            "currency",
            "phone_number",
            "address",
            "start_time",
            "end_time",
            "signature",
            "photos",
            "priority",
            "requirements",
            "customer_name",
            "is_paid",
            "is_overdue",
        ]
        read_only_fields = ["job_id", "created_at", "updated_at", "is_overdue"]
        extra_kwargs = {
            "title": {
                "error_messages": {
                    "required": "Job title is required.",
                    "blank": "Job title cannot be blank.",
                    "max_length": "Job title cannot exceed 100 characters.",
                }
            },
            "customer_name": {
                "error_messages": {
                    "required": "Customer name is required.",
                    "blank": "Customer name cannot be blank.",
                    "max_length": "Customer name cannot exceed 100 characters.",
                }
            },
            "phone_number": {
                "error_messages": {
                    "required": "A contact phone number is required for this job.",
                    "blank": "Contact phone number cannot be blank.",
                    "max_length": "Phone number is too long. It must be 15 characters or fewer.",
                }
            },
            "address": {
                "error_messages": {
                    "required": "A job address is required.",
                }
            },
            "start_time": {
                "error_messages": {
                    "required": "A start time is required.",
                    "invalid": "Start time format is invalid. Use ISO 8601 format (e.g. 2025-06-01T09:00:00Z).",
                }
            },
            "end_time": {
                "error_messages": {
                    "required": "An end time is required.",
                    "invalid": "End time format is invalid. Use ISO 8601 format (e.g. 2025-06-01T17:00:00Z).",
                }
            },
            "price": {
                "error_messages": {
                    "invalid": "Price must be a valid number (e.g. 150.00).",
                    "max_digits": "Price is too large. Maximum 10 digits allowed.",
                    "max_decimal_places": "Price can have at most 2 decimal places.",
                }
            },
        }

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Job title is required and cannot be blank.")
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Job title is too short. Please provide a more descriptive title (at least 3 characters)."
            )
        return value.strip()

    def validate_customer_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Customer name is required.")
        return value.strip()

    def validate_phone_number(self, value):
        if not value:
            raise serializers.ValidationError("A contact phone number is required for this job.")
        if not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain digits only. Remove any spaces, dashes, or special characters."
            )
        if len(value) != 10:
            raise serializers.ValidationError(
                f"Phone number must be exactly 10 digits long. You entered {len(value)} digit(s)."
            )
        return value

    def validate_address(self, value):
        if value is None:
            raise serializers.ValidationError("A job address is required.")
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Address must be provided as an object with location details (e.g. street, city, country)."
            )
        if not value:
            raise serializers.ValidationError(
                "Address cannot be empty. Please provide at least a street and city."
            )
        return value

    def validate_start_time(self, value):
        if value is None:
            raise serializers.ValidationError("A start time is required.")
        if value < timezone.now():
            raise serializers.ValidationError(
                "Start time cannot be in the past. Please select a future date and time."
            )
        return value

    def validate_end_time(self, value):
        if value is None:
            raise serializers.ValidationError("An end time is required.")
        if value < timezone.now():
            raise serializers.ValidationError(
                "End time cannot be in the past. Please select a future date and time."
            )
        return value

    def validate_signature(self, value):
        if value is None or value == "":
            return value
        if not (value.startswith("http://") or value.startswith("https://")):
            raise serializers.ValidationError(
                "Signature must be a valid URL starting with http:// or https://. "
                "Upload the signature image first and use the returned file key."
            )
        return value

    def validate_photos(self, value):
        if value is None:
            return value
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Photos must be a list of URL strings. "
                "Upload each photo first and use the returned file keys."
            )
        for index, photo in enumerate(value, start=1):
            if not isinstance(photo, str):
                raise serializers.ValidationError(
                    f"Photo {index} must be a string URL. Received type: {type(photo).__name__!r}."
                )
            if not (photo.startswith("http://") or photo.startswith("https://")):
                raise serializers.ValidationError(
                    f"Photo {index} must be a valid URL starting with http:// or https://."
                )
        return value

    def validate_requirements(self, value):
        if value is None:
            return value
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Requirements must be provided as a JSON object (key-value pairs)."
            )
        return value

    def validate_priority(self, value):
        if value not in VALID_PRIORITIES:
            valid_str = ", ".join(VALID_PRIORITIES)
            raise serializers.ValidationError(
                f"'{value}' is not a valid priority. Choose from: {valid_str}."
            )
        return value

    def validate_status(self, value):
        if value not in VALID_STATUSES:
            valid_str = ", ".join(VALID_STATUSES)
            raise serializers.ValidationError(
                f"'{value}' is not a valid job status. Choose from: {valid_str}."
            )
        return value

    def validate_currency(self, value):
        if value and value.upper() not in VALID_CURRENCIES:
            valid_str = ", ".join(VALID_CURRENCIES)
            raise serializers.ValidationError(
                f"'{value}' is not a supported currency code. Supported codes: {valid_str}."
            )
        return value.upper() if value else value

    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Price cannot be negative. Please enter a value of 0 or greater."
            )
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")

        if start_time and end_time:
            if end_time <= start_time:
                raise serializers.ValidationError(
                    {
                        "end_time": (
                            "End time must be after the start time. "
                            "Please select a valid time range."
                        )
                    }
                )

        return attrs

    def create(self, validated_data):
        job = Job.objects.create(**validated_data)
        return job

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.status = validated_data.get("status", instance.status)
        instance.assigned_to = validated_data.get("assigned_to", instance.assigned_to)
        instance.price = validated_data.get("price", instance.price)
        instance.currency = validated_data.get("currency", instance.currency)
        instance.phone_number = validated_data.get(
            "phone_number", instance.phone_number
        )
        instance.address = validated_data.get("address", instance.address)
        instance.start_time = validated_data.get("start_time", instance.start_time)
        instance.end_time = validated_data.get("end_time", instance.end_time)
        instance.signature = validated_data.get("signature", instance.signature)
        instance.photos = validated_data.get("photos", instance.photos)
        instance.customer_name = validated_data.get(
            "customer_name", instance.customer_name
        )
        instance.is_paid = validated_data.get("is_paid", instance.is_paid)
        instance.save()
        return instance

    def to_internal_value(self, data):
        if data.get("assigned_to") == "":
            mutable_data = data.copy() if hasattr(data, "copy") else data
            mutable_data["assigned_to"] = None
            return super().to_internal_value(mutable_data)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation.get("assigned_to") is None:
            representation["assigned_to"] = ""
        return representation
