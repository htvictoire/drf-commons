"""
Base serializers for testing.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializerForTesting(serializers.ModelSerializer):
    """Reusable test serializer for User model."""

    class Meta:
        model = User
        fields = "__all__"
