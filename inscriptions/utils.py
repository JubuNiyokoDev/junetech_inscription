from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import os
from .models import RegistrationVisitors, ImgRegistration
from .views import create_badge


def validate_registration(registration, request):
    """
    Valide une inscription, génère un badge et envoie un email de validation.
    Retourne un dictionnaire avec le résultat de la validation.
    """
    result = {
        "registration_number": registration.registration_number,
        "success": False,
        "badge_url": None,
        "email_sent": False,
        "error": None,
    }

    if registration.validation:
        result["error"] = "Inscription déjà validée."
        return result

    try:
        badge_path = os.path.join(settings.BASE_DIR, "static/images/badge_template.png")
        registration.validation = True
        registration.save()

        # Générer le badge
        badge_data = create_badge(registration, request, badge_path)

        # Assurer l'existence du dossier des badges
        badges_dir = os.path.join(settings.MEDIA_ROOT, "badges")
        os.makedirs(badges_dir, exist_ok=True)

        # Sauvegarder le badge
        badge_filename = f"{registration.registration_number}_badge.png"
        badge_filepath = os.path.join(badges_dir, badge_filename)
        with open(badge_filepath, "wb") as f:
            f.write(badge_data)
        badge_url = f"/media/badges/{badge_filename}"
        ImgRegistration.objects.create(
            registration_number=registration,
            url_img=badge_url,
        )
        result["badge_url"] = badge_url

        # Envoyer l'email de validation
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
        email_html = render_to_string("email/validation_email.html", context)
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
        result["email_sent"] = True
        result["success"] = True

    except FileNotFoundError as e:
        result["error"] = f"Modèle de badge introuvable : {e}"
    except Exception as e:
        result["error"] = f"Erreur lors de la validation : {str(e)}"

    return result
