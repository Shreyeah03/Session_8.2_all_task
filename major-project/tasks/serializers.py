from django.utils import timezone
from rest_framework import serializers

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "title", "description", "priority", "due_date", "status", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate_due_date(self, value):
        # Only block past dates when creating or when the date is actually being changed.
        changed = self.instance is None or self.instance.due_date != value
        if changed and value < timezone.localdate():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value
