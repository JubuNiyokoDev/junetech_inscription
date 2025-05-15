from django.contrib import admin
from .models import Participant, Scan
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import qrcode
from io import BytesIO
from PIL import Image
import os


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "prenom",
        "nom",
        "email",
        "numero_telephone",
        "date_inscription",
        "is_valid",
    )
    list_filter = ("date_inscription", "is_valid")
    search_fields = ("nom", "prenom", "email")
    readonly_fields = ("id", "date_inscription")
    actions = ["validate_participants"]

    def validate_participants(self, request, queryset):
        for participant in queryset:
            if not participant.is_valid:
                participant.is_valid = True
                participant.save()

                # Générer le QR code
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(
                    request.build_absolute_uri(
                        reverse("participant-detail", args=[participant.id])
                    )
                )
                qr.make(fit=True)
                qr_img = qr.make_image(fill="black", back_color="white")

                # Charger le badge template
                badge_path = os.path.join(
                    settings.BASE_DIR, "static/images/badge_template.png"
                )
                badge_img = Image.open(badge_path).convert("RGBA")

                # Redimensionner le QR code (ajustez la taille selon votre template)
                qr_size = (150, 150)  # Ajustez selon l'espace dans le badge
                qr_img = qr_img.resize(qr_size, Image.Resampling.LANCZOS)

                # Positionner le QR code (ajustez les coordonnées x, y)
                qr_position = (100, 200)  # Exemple : x=100, y=200
                badge_img.paste(qr_img, qr_position, qr_img)

                # Sauvegarder le badge
                buffer = BytesIO()
                badge_img.save(buffer, format="PNG")
                badge_data = buffer.getvalue()

                # Envoyer l'email de validation
                context = {
                    "prenom": participant.prenom,
                    "nom": participant.nom,
                    "badge_url": request.build_absolute_uri(
                        reverse("participant-badge", args=[participant.id])
                    ),
                }
                email_html = render_to_string("email/validation_email.html", context)
                email = EmailMessage(
                    subject="Votre Badge pour JuneTech 5ème Édition",
                    body=email_html,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[participant.email],
                )
                email.content_subtype = "html"
                email.attach(
                    f"badge_{participant.prenom}_{participant.nom}.png",
                    badge_data,
                    "image/png",
                )
                try:
                    email.send()
                except Exception as e:
                    self.message_user(
                        request,
                        f"Erreur lors de l'envoi de l'email à {participant.email} : {e}",
                        level="error",
                    )
                else:
                    self.message_user(
                        request, f"Participant {participant} validé et email envoyé."
                    )
        participant_count = queryset.count()
        self.message_user(request, f"{participant_count} participant(s) validé(s).")

    validate_participants.short_description = "Valider les participants sélectionnés"


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ("participant", "type_scan", "jour_evenement", "date_scan")
    list_filter = ("type_scan", "jour_evenement")
    search_fields = ("participant__nom", "participant__prenom")
