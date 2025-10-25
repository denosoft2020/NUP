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
    PollingStationListCreateView,
    DRFormListCreateView,
    create_agent,
    AgentCreateView,
    reports_list,
    current_user, 
)
from . import views

urlpatterns = [
    # JWT Auth
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('agents/create/', create_agent, name='create_agent'),
    # path('agents/create/', AgentCreateView.as_view(), name='agent-create'),
    #path('create_agent/', views.create_agent, name='create_agent'),
    path("user/", CurrentUserView.as_view(), name="current_user"),
    # DR Form Endpoints
    path('api/pollingstations/', PollingStationListCreateView.as_view(), name='pollingstation-list'),
    path("drforms/", DRFormListCreateView.as_view(), name="drform-list"),      # ✅ list all /api/drforms/?verified=true&page=1
    path('pollingstations/', PollingStationListCreateView.as_view()),
    path("drforms/upload/", DRFormUploadView.as_view(), name="drform-upload"),
    path("pending/", PendingListView.as_view(), name="pending-list"),
    path("drforms/<int:pk>/verify/", DRFormVerifyView.as_view(), name="drform-verify"),
    path("verified/", VerifiedListView.as_view(), name="verified-list"),
    path("drforms/public/", PublicFeedView.as_view(), name="drform-public"),

    # Admin and Public
    path("public_feed/", PublicFeedView.as_view(), name="public-feed"),
    path("users/", UserListView.as_view(), name="user_list"),
    path('reports/', reports_list, name='reports_list'),
    path('agents/register/', views.register_agent, name='register_agent'),
    path('agents/', views.list_agents, name='list_agents'),
    path('polling_stations/', views.polling_stations, name='polling_stations'),
    path('nup/news/', views.nup_news, name='nup_news'),
    path("results/summary/", views.results_summary, name="results_summary"),

]
