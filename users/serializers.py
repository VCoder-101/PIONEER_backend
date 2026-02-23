from rest_framework import serializers
from .models import User, UserSession, AuthCode


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'role', 'is_active', 'privacy_policy_accepted_at', 'created_at', 'last_login_at']
        read_only_fields = ['id', 'created_at', 'last_login_at']


class UserSessionSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = UserSession
        fields = ['id', 'user', 'user_phone', 'device_id', 'ip_address', 'user_agent', 'created_at', 'expires_at', 'is_active']
        read_only_fields = ['id', 'created_at']


class AuthCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthCode
        fields = ['id', 'phone', 'attempts_left', 'is_used', 'created_at', 'expires_at']
        read_only_fields = ['id', 'created_at']
