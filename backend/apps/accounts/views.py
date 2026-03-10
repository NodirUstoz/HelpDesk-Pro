"""
Views for authentication and user management.
"""
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User, Agent, Customer, Team
from .permissions import IsAdmin, IsAdminOrAgent
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    AgentSerializer,
    CustomerSerializer,
    TeamSerializer,
)


class RegisterView(generics.CreateAPIView):
    """Register a new user account."""

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": serializer.get_tokens(user),
                "message": "Registration successful.",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    """Authenticate user and return JWT tokens."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        user.is_online = True
        user.last_activity = timezone.now()
        user.save(update_fields=["is_online", "last_activity"])

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(generics.GenericAPIView):
    """Blacklist the refresh token to log out."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            request.user.is_online = False
            request.user.save(update_fields=["is_online"])

            return Response(
                {"message": "Logged out successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"message": "Logged out successfully."},
                status=status.HTTP_200_OK,
            )


class MeView(generics.RetrieveUpdateAPIView):
    """Get or update the current user's profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class PasswordChangeView(generics.GenericAPIView):
    """Change the current user's password."""

    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.ModelViewSet):
    """Admin-level user management."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["role", "is_active", "is_online"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["created_at", "email", "last_activity"]


class AgentViewSet(viewsets.ModelViewSet):
    """Manage agent profiles."""

    queryset = Agent.objects.select_related("user", "team").all()
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAgent]
    filterset_fields = ["availability", "team"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "department"]

    @action(detail=True, methods=["post"])
    def set_availability(self, request, pk=None):
        agent = self.get_object()
        availability = request.data.get("availability")
        if availability not in dict(Agent.Availability.choices):
            return Response(
                {"error": "Invalid availability status."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        agent.availability = availability
        agent.save(update_fields=["availability"])
        return Response(AgentSerializer(agent).data)

    @action(detail=False, methods=["get"])
    def available(self, request):
        agents = self.queryset.filter(availability=Agent.Availability.ONLINE)
        serializer = self.get_serializer(agents, many=True)
        return Response(serializer.data)


class CustomerViewSet(viewsets.ModelViewSet):
    """Manage customer profiles."""

    queryset = Customer.objects.select_related("user").all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAgent]
    filterset_fields = ["is_vip", "company"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "company"]


class TeamViewSet(viewsets.ModelViewSet):
    """Manage teams."""

    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAgent]
    filterset_fields = ["is_active", "assignment_method"]
    search_fields = ["name"]
