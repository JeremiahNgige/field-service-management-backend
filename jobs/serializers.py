from rest_framework import serializers
from .models import Job
from django.utils import timezone


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
            "author",
            "technician",
            "phone_number",
            "address",
            "start_time",
            "end_time",
            "signature",
            "photos",
            "priority",
            "requirements",
        ]
        read_only_fields = ["job_id", "created_at", "updated_at"]

    def validate_phone_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits.")
        if len(value) != 10:
            raise serializers.ValidationError("Phone number must be 10 digits long.")
        return value

    def validate_address(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Address must be a dictionary.")
        return value

    def validate_start_time(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Start time cannot be in the past.")
        return value

    def validate_end_time(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("End time cannot be in the past.")
        return value

    def validate_signature(self, value):
        if not value.startswith("http"):
            raise serializers.ValidationError("Signature must be a valid URL.")
        return value

    def validate_photos(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Photos must be a list.")
        for photo in value:
            if not photo.startswith("http"):
                raise serializers.ValidationError("Photo must be a valid URL.")
        return value

    def validate_requirements(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Requirements must be a dictionary.")
        return value

    def validate_priority(self, value):
        if value not in ["low", "medium", "high"]:
            raise serializers.ValidationError("Priority must be low, medium, or high.")
        return value

    def create(self, validated_data):
        job = Job.objects.create(**validated_data)
        return job

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.status = validated_data.get("status", instance.status)
        instance.author = validated_data.get("author", instance.author)
        instance.technician = validated_data.get("technician", instance.technician)
        instance.phone_number = validated_data.get(
            "phone_number", instance.phone_number
        )
        instance.address = validated_data.get("address", instance.address)
        instance.start_time = validated_data.get("start_time", instance.start_time)
        instance.end_time = validated_data.get("end_time", instance.end_time)
        instance.signature = validated_data.get("signature", instance.signature)
        instance.photos = validated_data.get("photos", instance.photos)
        instance.save()
        return instance
