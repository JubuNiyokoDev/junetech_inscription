from django.urls import path
from .views import (
    ParticipantCreateView,
    ParticipantDetailView,
    ScanCreateView,
    ScanSummaryView,
    generate_badge,
)

urlpatterns = [
    path(
        "api/participants/", ParticipantCreateView.as_view(), name="participant-create"
    ),
    path(
        "api/participants/<uuid:id>/",
        ParticipantDetailView.as_view(),
        name="participant-detail",
    ),
    path("api/scans/", ScanCreateView.as_view(), name="scan-create"),
    path("api/scans/summary/", ScanSummaryView.as_view(), name="scan-summary"),
    path("api/participants/<uuid:id>/badge/", generate_badge, name="participant-badge"),
]
