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
from .views import create_badge


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
        badge_path = os.path.join(settings.BASE_DIR, "static/images/badge_template.png")

        for registration in queryset:
            if not registration.validation:
                try:
                    registration.validation = True
                    registration.save()

                    # Generate badge using centralized function
                    badge_data = create_badge(registration, request, badge_path)

                    # Ensure badges directory exists
                    badges_dir = os.path.join(settings.MEDIA_ROOT, "badges")
                    os.makedirs(badges_dir, exist_ok=True)

                    # Save badge to media folder
                    badge_filename = f"{registration.registration_number}_badge.png"
                    badge_filepath = os.path.join(badges_dir, badge_filename)
                    with open(badge_filepath, "wb") as f:
                        f.write(badge_data)
                    badge_url = f"/media/badges/{badge_filename}"
                    ImgRegistration.objects.create(
                        registration_number=registration,
                        url_img=badge_url,
                    )

                    # Send validation email
                    context = {
                        "first_name": registration.first_name,
                        "name": registration.name,
                        "badge_url": request.build_absolute_uri(
                            reverse(
                                "registration-badge",
                                args=[registration.registration_number],
                            )
                        ),
                    }
                    email_html = render_to_string(
                        "email/validation_email.html", context
                    )
                    email = EmailMessage(
                        subject="Votre Badge pour JuneTech 5ème Édition",
                        body=email_html,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[registration.email],
                    )
                    email.content_subtype = "html"
                    email.attach(
                        f"badge_{registration.first_name}_{registration.name}.png",
                        badge_data,
                        "image/png",
                    )
                    email.send()
                    validated_count += 1
                    self.message_user(
                        request,
                        f"Registration {registration} validée et email envoyé.",
                        level=messages.SUCCESS,
                    )
                except FileNotFoundError as e:
                    self.message_user(
                        request,
                        f"Erreur pour {registration.email} : {e}",
                        level=messages.ERROR,
                    )
                except Exception as e:
                    self.message_user(
                        request,
                        f"Erreur lors de la validation de {registration.email} : {e}",
                        level=messages.ERROR,
                    )
        if validated_count > 0:
            self.message_user(
                request,
                f"{validated_count} registration(s) validée(s) avec succès.",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "Aucune registration validée (déjà validées ou erreurs).",
                level=messages.WARNING,
            )

    validate_registrations.short_description = "Valider les registrations sélectionnées"
