from django.shortcuts import render

# Create your views here.
import hashlib
from rest_framework import generics, status, filters, viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from .models import DRForm, PollingStation, User
from .serializers import DRFormUploadSerializer, DRFormPublicSerializer, DRFormSerializer, UserSerializer
from .permissions import IsAgent
from django.shortcuts import get_object_or_404
from django.db.models import Q

class DRFormUploadView(generics.CreateAPIView):
    serializer_class = DRFormUploadSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsAgent, IsAdminUser]

    def perform_create(self, serializer):
        # Save uploaded_by and let post-save verification happen
        serializer.save(uploaded_by=self.request.user)

    def create(self, request, *args, **kwargs):
        # Additional server-side hash verification
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image_file = request.FILES.get('image')
        provided_hash = serializer.validated_data.get('sha256_hash')

        # compute server hash to verify integrity
        sha256 = hashlib.sha256()
        for chunk in image_file.chunks():
            sha256.update(chunk)
        computed_hash = sha256.hexdigest()

        if provided_hash and provided_hash != computed_hash:
            return Response({'detail': 'Hash mismatch'}, status=status.HTTP_400_BAD_REQUEST)

        # Save object
        obj = serializer.save(uploaded_by=request.user, sha256_hash=computed_hash)
        return Response({'id': obj.id, 'sha256_hash': computed_hash, 'status': 'uploaded'}, status=status.HTTP_201_CREATED)

class DRFormVerifyView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    queryset = DRForm.objects.all()
    lookup_field = 'pk'

    def post(self, request, pk):
        try:
            dr_form = self.get_object()
            dr_form.verified = True
            dr_form.verified_by = request.user
            dr_form.save()
            return Response({"success": True, "id": dr_form.id})
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
    serializer_class = DRFormPublicSerializer
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