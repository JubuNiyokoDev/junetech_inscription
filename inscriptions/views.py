from django.shortcuts import render
from rest_framework import generics, views
from rest_framework.response import Response
from .models import RegistrationVisitors, Scan, Event, RegistrationType, ImgRegistration
from .serializers import RegistrationVisitorsSerializer, ScanSerializer
from rest_framework.permissions import AllowAny
import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.urls import reverse
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
from rest_framework import status
from rest_framework import serializers
from django.shortcuts import get_object_or_404, redirect
from .utils import validate_registration


def registration_badge_view(request, registration_number):
    img = get_object_or_404(ImgRegistration, registration_number=registration_number)
    return redirect(img.url_img)


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


class RegistrationCreateView(generics.CreateAPIView):
    queryset = RegistrationVisitors.objects.all()
    serializer_class = RegistrationVisitorsSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        registration = serializer.save()
        context = {
            "first_name": registration.first_name,
            "name": registration.name,
        }
        email_html = render_to_string("email/confirmation_email.html", context)
        email = EmailMessage(
            subject="Confirmation de votre inscription à JuneTech 5ème Édition",
            body=email_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[registration.email],
        )
        email.content_subtype = "html"
        try:
            email.send()
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email : {e}")


class RegistrationDetailView(generics.RetrieveAPIView):
    queryset = RegistrationVisitors.objects.all()
    serializer_class = RegistrationVisitorsSerializer
    lookup_field = "registration_number"
    permission_classes = [AllowAny]


class ScanCreateView(generics.CreateAPIView):
    queryset = Scan.objects.all()
    serializer_class = ScanSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        try:
            serializer.save()
        except Exception as e:
            raise serializers.ValidationError(
                f"Erreur lors de l'enregistrement du scan : {str(e)}"
            )


class ScanDeleteView(generics.DestroyAPIView):
    queryset = Scan.objects.all()
    serializer_class = ScanSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"

    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {"message": "Scan supprimé avec succès"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la suppression : {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ScanSummaryView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        jour_evenement = request.query_params.get("jour_evenement", None)
        filters = {}
        if jour_evenement:
            filters["jour_evenement"] = jour_evenement

        total_entrees = Scan.objects.filter(type_scan="ENTREE", **filters).count()
        total_sorties = Scan.objects.filter(type_scan="SORTIE", **filters).count()

        scans = Scan.objects.filter(**filters).select_related("registration")
        scan_list = [
            {
                "id": scan.id,
                "registration": f"{scan.registration.first_name} {scan.registration.name} ({scan.registration.registration_number})",
                "type_scan": scan.type_scan,
                "jour_evenement": scan.jour_evenement,
                "date_scan": scan.date_scan,
            }
            for scan in scans
        ]

        return Response(
            {
                "total_entrees": total_entrees,
                "total_sorties": total_sorties,
                "scans": scan_list,
            }
        )


class RegistrationValidateView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        registration_numbers = request.data.get("registration_numbers", [])
        if not registration_numbers:
            return Response(
                {"error": "Aucun numéro d'inscription valide fourni."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated = []
        errors = []
        for reg_number in registration_numbers:
            try:
                registration = RegistrationVisitors.objects.get(
                    registration_number=reg_number
                )
                result = validate_registration(registration, request)
                if result["success"]:
                    validated.append(
                        {
                            "registration_number": reg_number,
                            "badge_url": result["badge_url"],
                            "email_sent": result["email_sent"],
                        }
                    )
                else:
                    errors.append(
                        {"registration_number": reg_number, "error": result["error"]}
                    )
            except RegistrationVisitors.DoesNotExist:
                errors.append(
                    {
                        "registration_number": reg_number,
                        "error": "Inscription non trouvée.",
                    }
                )

        response_data = {
            "message": f"{len(validated)} inscription(s) validée(s) avec succès.",
            "validated": validated,
            "errors": errors,
        }
        status_code = status.HTTP_200_OK if validated else status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=status_code)


def home(request):
    for reg in Event.objects.all():
        print(f"ID: {reg.id_event}, Nom: '{reg.title_fr}'")
    return render(
        request,
        "home.html",
        {
            "events": Event.objects.filter(date_start_event__gte=datetime.now().date()),
            "registration_types": RegistrationType.objects.all(),
        },
    )


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
