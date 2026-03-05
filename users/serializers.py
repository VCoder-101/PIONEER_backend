from rest_framework import serializers
from .models import User, UserSession


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'is_active', 'privacy_policy_accepted_at', 'created_at', 'last_login_at']
        read_only_fields = ['id', 'created_at', 'last_login_at']


class UserSessionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserSession
        fields = ['id', 'email', 'name', 'role', 'is_active', 'privacy_policy_accepted_at', 'created_at', 'last_login_at']
        read_only_fields = ['id', 'created_at']
