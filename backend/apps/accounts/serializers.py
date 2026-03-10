"""
Serializers for User, Agent, Customer, Team models.
"""
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Agent, Customer, Team


class TeamSerializer(serializers.ModelSerializer):
    agent_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id", "name", "description", "assignment_method",
            "is_active", "agent_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_agent_count(self, obj):
        return obj.agents.count()


class AgentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    team_name = serializers.CharField(source="team.name", read_only=True, default=None)

    class Meta:
        model = Agent
        fields = [
            "id", "user", "user_email", "user_name", "team", "team_name",
            "department", "specialization", "availability",
            "max_concurrent_chats", "max_concurrent_tickets",
            "current_ticket_count", "current_chat_count",
            "total_tickets_resolved", "average_rating",
            "is_available_for_chat", "is_available_for_ticket",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "current_ticket_count", "current_chat_count",
            "total_tickets_resolved", "average_rating", "created_at", "updated_at",
        ]


class CustomerSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id", "user", "user_email", "user_name", "company", "website",
            "notes", "timezone_str", "language", "total_tickets", "is_vip",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "total_tickets", "created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    agent_profile = AgentSerializer(read_only=True)
    customer_profile = CustomerSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "role",
            "avatar", "phone", "is_online", "last_activity",
            "agent_profile", "customer_profile",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_online", "last_activity", "created_at", "updated_at"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    tokens = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "password",
            "password_confirm", "role", "phone", "tokens",
        ]
        read_only_fields = ["id", "tokens"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        role = validated_data.get("role", User.Role.CUSTOMER)
        user = User.objects.create_user(**validated_data)

        # Auto-create profile based on role
        if role == User.Role.AGENT:
            Agent.objects.create(user=user)
        elif role == User.Role.CUSTOMER:
            Customer.objects.create(user=user)

        return user

    def get_tokens(self, obj):
        refresh = RefreshToken.for_user(obj)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )
        if not user:
            raise serializers.ValidationError(
                "Unable to log in with provided credentials."
            )
        if not user.is_active:
            raise serializers.ValidationError("This account is deactivated.")

        attrs["user"] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
