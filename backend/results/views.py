from django.shortcuts import render

# Create your views here.
import hashlib
from rest_framework import generics, status, filters, viewsets, permissions, parsers
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from .models import DRForm, PollingStation, User, Report, AbstractUser, Agent, NupNews, Result
from .serializers import DRFormUploadSerializer, DRFormPublicSerializer, DRFormSerializer, UserSerializer, PollingStationSerializer, ReportSerializer,AgentSerializer, AgentRegisterSerializer, NupNewsSerializer
from .permissions import IsAgent
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum


class DRFormUploadView(generics.CreateAPIView):
    serializer_class = DRFormUploadSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_file = request.FILES.get('image')
        provided_hash = serializer.validated_data.get('sha256_hash')

        # Verify hash
        if image_file:
            sha256 = hashlib.sha256()
            for chunk in image_file.chunks():
                sha256.update(chunk)
            computed_hash = sha256.hexdigest()

            if provided_hash and provided_hash != computed_hash:
                return Response({'detail': 'Hash mismatch'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            computed_hash = None

        obj = serializer.save(uploaded_by=request.user, sha256_hash=computed_hash)
        return Response({
            'id': obj.id,
            'polling_station': str(obj.polling_station),
            'sha256_hash': computed_hash,
            'status': 'uploaded'
        }, status=status.HTTP_201_CREATED)
    
class PollingStationListCreateView(generics.ListCreateAPIView):
    queryset = PollingStation.objects.all()
    serializer_class = PollingStationSerializer
    filterset_fields = ['station_id']

class DRFormVerifyView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    queryset = DRForm.objects.all()
    lookup_field = 'pk'

    def post(self, request, pk):
        try:
            dr_form = DRForm.objects.get(pk=pk)
            dr_form.verified = True
            dr_form.verified_by = request.user
            dr_form.save()
            return Response({"success": True, "id": dr_form.id,  "verified_by": str(request.user)}, status=status.HTTP_200_OK)
        except DRForm.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

class SmallPagination(PageNumberPagination):
    page_size = 20  # or any small number for testing


class PublicFeedView(generics.ListAPIView):
    serializer_class = DRFormPublicSerializer
    permission_classes = (AllowAny,)
    # Serve the full public feed (no pagination) so frontend can fetch all posts
    pagination_class = SmallPagination

    def get_queryset(self):
        # Only show verified forms to public
        return DRForm.objects.filter(verified=True).order_by('-id')

class PendingListView(generics.ListAPIView):
    queryset = DRForm.objects.filter(Q(verified=False) | Q(verified__isnull=True)).order_by('-timestamp')
    serializer_class = DRFormSerializer
    pagination_class = None  

class VerifiedListView(generics.ListAPIView):
    queryset = DRForm.objects.filter(verified=True)
    serializer_class = DRFormSerializer

    
class SafePaginator(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except Exception:
            # if page out of range, return empty
            self.page = None
            return []
    
class DRFormPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20


class DRFormListView(generics.ListAPIView):
    """
    Public feed view that supports infinite scroll via pagination.
    Returns only verified DR forms, ordered by most recent.
    """
    serializer_class = DRFormSerializer
    permission_classes = (AllowAny,)
    pagination_class = DRFormPagination

    def get_queryset(self):
        verified = self.request.query_params.get("verified", "true")
        queryset = DRForm.objects.filter(verified=(verified.lower() == "true")).order_by("-timestamp")
        return queryset
    
class UserListView(generics.ListAPIView):
    """List all users (for admin)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

class CurrentUserView(generics.RetrieveAPIView):
    """Get current logged-in user."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

class DRFormListCreateView(generics.ListCreateAPIView):
    queryset = DRForm.objects.all()
    serializer_class = DRFormSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

class AgentCreateView(generics.CreateAPIView):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [permissions.AllowAny]

@api_view(['GET'])
def reports_list(request):
    status = request.GET.get('status')
    if status == 'verified':
        reports = Report.objects.filter(status='verified')
    elif status == 'pending':
        reports = Report.objects.filter(status='pending')
    else:
        reports = Report.objects.all()

    serializer = ReportSerializer(reports, many=True)
    return Response(serializer.data)

@api_view(["POST"])
def register_agent(request):
    serializer = AgentRegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Agent registered successfully!"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def list_agents(request):
    agents = Agent.objects.all()
    serializer = AgentSerializer(agents, many=True)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
def polling_stations(request):
    if request.method == 'GET':
        stations = PollingStation.objects.all()
        serializer = PollingStationSerializer(stations, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = PollingStationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])  # ✅ Only admins can create agents
def create_agent(request):
    data = request.data

    # ✅ Validate required fields
    required_fields = [
        'full_name', 'phone', 'email', 'district', 'constituency', 'polling_station'
    ]
    for field in required_fields:
        if field not in data or not data[field].strip():
            return Response(
                {"error": f"Missing required field: {field}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # ✅ Create or get PollingStation automatically
    station, created = PollingStation.objects.get_or_create(
        name=data['polling_station'],
        defaults={
            'station_id': f"PS-{Agent.objects.count() + 1}",
            'district': data['district'],
            'constituency': data['constituency']
        }
    )

    # ✅ Create a new user account for the agent
    if User.objects.filter(username=data['email']).exists():
        return Response({"error": "User with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=data['email'],
        email=data['email'],
        password='agent123',
        is_agent=True
    )

    # ✅ Create Agent profile
    agent = Agent.objects.create(
        user=user,
        full_name=data['full_name'],
        phone=data['phone'],
        email=data['email'],
        district=data['district'],
        constituency=data['constituency'],
        polling_station=station
    )

    serializer = AgentSerializer(agent)

    return Response({
        "message": "✅ Agent created successfully.",
        "agent": serializer.data,
        "login_credentials": {
            "username": user.username,
            "password": "agent123"
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['GET', 'POST'])
def nup_news(request):
    if request.method == 'GET':
        news = NupNews.objects.all().order_by('-created_at')
        serializer = NupNewsSerializer(news, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = NupNewsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@api_view(['GET'])
def results_summary(request):
    """
    Returns total votes for NUP and NRM across all DR forms.
    """
    nup_total = 0
    nrm_total = 0

    forms = DRForm.objects.all()
    for form in forms:
        totals = form.totals or {}
        nup_total += int(totals.get("NUP", 0))
        nrm_total += int(totals.get("NRM", 0))

    data = [
        {"party": "NUP", "votes": nup_total},
        {"party": "NRM", "votes": nrm_total}
    ]
    return Response(data)
