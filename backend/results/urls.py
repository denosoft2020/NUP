from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    DRFormUploadView,
    DRFormVerifyView,
    DRFormListView,     # <-- Make sure this view exists
    PublicFeedView,
    PendingListView,
    UserListView,
    VerifiedListView,
    CurrentUserView,
    current_user, 
)

urlpatterns = [
    # JWT Auth
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("user/", CurrentUserView.as_view(), name="current_user"),
    # DR Form Endpoints
    path("drforms/", DRFormListView.as_view(), name="drform-list"),      # ✅ list all /api/drforms/?verified=true&page=1
    path("drforms/upload/", DRFormUploadView.as_view(), name="drform-upload"),
    path("pending/", PendingListView.as_view(), name="pending-list"),
    path("drforms/<int:pk>/verify/", DRFormVerifyView.as_view(), name="drform-verify"),
    path("verified/", VerifiedListView.as_view(), name="verified-list"),
    path("drforms/public/", PublicFeedView.as_view(), name="drform-public"),

    # Admin and Public
    path("public_feed/", PublicFeedView.as_view(), name="public-feed"),
    path("users/", UserListView.as_view(), name="user_list"),


]
