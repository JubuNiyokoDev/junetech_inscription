from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import os
from .models import ImgRegistration, RegistrationVisitors
from .models import ImgRegistration
import qrcode
from io import BytesIO
from django.urls import reverse
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from PIL import Image, ImageDraw, ImageFont


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


def create_badge(registration, request, badge_path):
    # === Données QR Code ===
    qr_data = request.build_absolute_uri(
        reverse("registration-detail", args=[registration.registration_number])
    ).rstrip("/")
    qr = qrcode.QRCode(version=1, box_size=15, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill="black", back_color="white")

    # === Vérification modèle ===
    if not os.path.exists(badge_path):
        raise FileNotFoundError(f"Modèle introuvable : {badge_path}")

    badge_img = Image.open(badge_path).convert("RGBA")
    badge_width, badge_height = badge_img.size
    max_width = badge_width * 0.9
    draw = ImageDraw.Draw(badge_img)

    # === Chargement de la police ===
    font_path = os.path.join(settings.BASE_DIR, "static/fonts/arialbd.ttf")
    if not os.path.exists(font_path):
        font_path = os.path.join(settings.BASE_DIR, "static/fonts/Lato-Bold.ttf")

    # === QR Code positionné en bas ===
    qr_size = (700, 700)
    scale_factor = 1.5
    qr_size_scaled = (int(qr_size[0] * scale_factor), int(qr_size[1] * scale_factor))
    qr_img = qr_img.resize(qr_size_scaled, Image.Resampling.BICUBIC)
    qr_x = badge_width // 2 - qr_size[0] // 2
    qr_y = 3350  # position ajustée selon le design final
    badge_img.paste(qr_img, (qr_x, qr_y))

    # === Nom Complet ===
    full_name = f"{registration.name.upper()} {registration.first_name}"
    name_font_size = 250
    while True:
        try:
            font_name = ImageFont.truetype(font_path, size=name_font_size)
        except:
            font_name = ImageFont.load_default()
        name_bbox = draw.textbbox((0, 0), full_name, font=font_name)
        name_width = name_bbox[2] - name_bbox[0]
        if name_width <= max_width or name_font_size <= 100:
            break
        name_font_size -= 5

    name_x = badge_width // 2 - name_width // 2
    name_y = 2850
    draw.text((name_x, name_y), full_name, fill="white", font=font_name)

    # === Statut 1 (ex: ENTREPRISE) ===
    statut_part1 = registration.id_type.name_fr.upper()
    statut_font_size = 280
    letter_spacing = 30
    letters = list(statut_part1)
    while True:
        try:
            font_statut = ImageFont.truetype(font_path, size=statut_font_size)
        except:
            font_statut = ImageFont.load_default()
        total_width = 0
        letter_positions = []
        for letter in letters:
            bbox = draw.textbbox((0, 0), letter, font=font_statut)
            letter_width = bbox[2] - bbox[0]
            letter_positions.append((letter, total_width))
            total_width += letter_width + letter_spacing
        if total_width <= max_width or statut_font_size <= 150:
            break
        statut_font_size -= 5

    start_x = badge_width // 2 - total_width // 2
    y_statut1 = 4500
    for letter, offset in letter_positions:
        draw.text((start_x + offset, y_statut1), letter, fill="white", font=font_statut)

    # === Statut 2 (ex: Université) ===
    statut_part2 = registration.name_organization or "Université"
    societe_font_size = 100
    while True:
        try:
            font_societe = ImageFont.truetype(font_path, size=societe_font_size)
        except:
            font_societe = ImageFont.load_default()
        statut_bbox2 = draw.textbbox((0, 0), statut_part2, font=font_societe)
        statut_width2 = statut_bbox2[2] - statut_bbox2[0]
        if statut_width2 <= max_width or societe_font_size <= 60:
            break
        societe_font_size -= 5

    statut_x = badge_width // 2 - statut_width2 // 2
    statut_y = 4900
    draw.text((statut_x, statut_y), statut_part2, fill="white", font=font_societe)

    # === Agrandir tout le badge ===
    new_width = int(badge_img.width * scale_factor)
    new_height = int(badge_img.height * scale_factor)
    badge_img = badge_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # === Sauvegarde dans un buffer mémoire ===
    buffer = BytesIO()
    badge_img.save(buffer, format="PNG", dpi=(300, 300))
    return buffer.getvalue()


def generate_badge(request, registration_number):
    try:
        registration = RegistrationVisitors.objects.get(
            registration_number=registration_number
        )
        if not registration.validation:
            return HttpResponse(
                "Utilisateur non trouvé ou non validé.",
                status=404,
                content_type="text/plain",
            )
    except RegistrationVisitors.DoesNotExist:
        return HttpResponse(
            "Utilisateur non trouvé.", status=404, content_type="text/plain"
        )

    badge_path = os.path.join(settings.BASE_DIR, "static/images/badge_template.png")
    try:
        badge_data = create_badge(registration, request, badge_path)
    except FileNotFoundError as e:
        return HttpResponse(f"{e}", status=500, content_type="text/plain")

    response = HttpResponse(badge_data, content_type="image/png")
    response["Content-Disposition"] = (
        f"attachment; filename=badge_{registration.first_name}_{registration.name}.png"
    )
    return response
