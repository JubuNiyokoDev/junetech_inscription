from django.contrib import admin
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import os
from django.contrib import messages
from .models import (
    Event,
    TypeEvent,
    RegistrationType,
    RegistrationVisitors,
    ImgRegistration,
    Scan,
)
from .utils import validate_registration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title_fr",
        "date_start_event",
        "date_stop_event",
        "localisation",
        "published",
    )
    list_filter = ("published", "date_start_event")
    search_fields = ("title_fr", "title_en")


@admin.register(TypeEvent)
class TypeEventAdmin(admin.ModelAdmin):
    list_display = ("name_fr", "name_en", "date_create")
    search_fields = ("name_fr", "name_en")


@admin.register(RegistrationType)
class RegistrationTypeAdmin(admin.ModelAdmin):
    list_display = ("name_fr", "name_en", "date_create")
    search_fields = ("name_fr", "name_en")


@admin.register(ImgRegistration)
class ImgRegistrationAdmin(admin.ModelAdmin):
    list_display = ("registration_number", "url_img", "date_create")
    search_fields = ("registration_number__registration_number",)


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ("registration", "type_scan", "jour_evenement", "date_scan")
    list_filter = ("type_scan", "jour_evenement")
    search_fields = (
        "registration__name",
        "registration__first_name",
        "registration__registration_number",
    )


@admin.register(RegistrationVisitors)
class RegistrationVisitorsAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "name",
        "email",
        "id_event",
        "id_type",
        "registration_number",
        "validation",
        "date_registration",
    )
    list_filter = ("validation", "date_registration", "id_event", "id_type")
    search_fields = ("name", "first_name", "email", "registration_number")
    readonly_fields = (
        "id_registration",
        "date_registration",
        "registration_number",
        "date_validation",
    )
    actions = ["validate_registrations"]

    def validate_registrations(self, request, queryset):
        validated_count = 0
        for registration in queryset:
            result = validate_registration(registration, request)
            if result["success"]:
                validated_count += 1
                self.message_user(
                    request,
                    f"Inscription {registration} validée et email envoyé.",
                    level=messages.SUCCESS,
                )
            else:
                self.message_user(
                    request,
                    f"Erreur pour {registration.email} : {result['error']}",
                    level=messages.ERROR,
                )
        if validated_count > 0:
            self.message_user(
                request,
                f"{validated_count} inscription(s) validée(s) avec succès.",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "Aucune inscription validée (déjà validées ou erreurs).",
                level=messages.WARNING,
            )

    validate_registrations.short_description = "Valider les inscriptions sélectionnées"
