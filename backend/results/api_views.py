import hashlib
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import DRForm
from .serializers import DRFormUploadSerializer, DRFormPublicSerializer
from .permissions import IsAgent
from django.shortcuts import get_object_or_404

class DRFormUploadView(generics.CreateAPIView):
    serializer_class = DRFormUploadSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAuthenticated, IsAgent)

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

class DRFormVerifyView(generics.UpdateAPIView):
    # Admin endpoint to mark a DRForm as verified
    queryset = DRForm.objects.all()
    serializer_class = DRFormPublicSerializer
    permission_classes = (IsAuthenticated,)

    def patch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({'detail': 'Only staff can verify'}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        instance.verified = True
        instance.verified_by = request.user
        instance.save()
        return Response({'status': 'verified', 'id': instance.id})

class PublicFeedView(generics.ListAPIView):
    serializer_class = DRFormPublicSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        # Only show verified forms to public
        return DRForm.objects.filter(verified=True).select_related('polling_station', 'verified_by')

class PendingListView(generics.ListAPIView):
    serializer_class = DRFormPublicSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # Only staff/admins should access pending
        if self.request.user.is_staff:
            return DRForm.objects.filter(verified=False)
        return DRForm.objects.none()
    