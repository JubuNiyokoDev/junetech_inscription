from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "api/registrations/",
        views.RegistrationCreateView.as_view(),
        name="registration-create",
    ),
    path(
        "api/registrations/<str:registration_number>/",
        views.RegistrationDetailView.as_view(),
        name="registration-detail",
    ),
    path(
        "api/registrations/validate/",
        views.RegistrationValidateView.as_view(),
        name="registration-validate",
    ),
    path("api/scans/", views.ScanCreateView.as_view(), name="scan-create"),
    path("api/scans/<int:id>/", views.ScanDeleteView.as_view(), name="scan-delete"),
    path("api/scan-summary/", views.ScanSummaryView.as_view(), name="scan-summary"),
    path(
        "api/registrations/<str:registration_number>/badge/",
        views.generate_badge,
        name="generate-badge",
    ),
    path(
        "api/registrations/<str:registration_number>/badge-url/",
        views.registration_badge_view,
        name="registration-badge",
    ),
]
