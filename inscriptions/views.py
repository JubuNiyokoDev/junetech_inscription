from django.shortcuts import render
from rest_framework import generics, views
from rest_framework.response import Response
from .models import RegistrationVisitors, Scan, Event, RegistrationType
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


def create_badge(registration, request, badge_path):
    qr = qrcode.QRCode(version=1, box_size=15, border=5)
    qr_data = request.build_absolute_uri(
        reverse("registration-detail", args=[registration.registration_number])
    ).rstrip("/")
    print(f"QR code data: {qr_data}")
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill="black", back_color="white")

    if not os.path.exists(badge_path):
        raise FileNotFoundError(f"Badge template not found at {badge_path}")

    badge_img = Image.open(badge_path).convert("RGBA")
    badge_width = badge_img.width
    max_width = badge_width * 0.9

    qr_size = (280, 280)
    qr_img = qr_img.resize(qr_size, Image.Resampling.BICUBIC)
    qr_position = (
        badge_img.width // 2 - qr_size[0] // 2,
        1080,
    )
    badge_img.paste(qr_img, qr_position, qr_img)

    draw = ImageDraw.Draw(badge_img)
    try:
        font_path = os.path.join(settings.BASE_DIR, "static/fonts/arialbd.ttf")
        if not os.path.exists(font_path):
            font = ImageFont.load_default()
        else:
            font = ImageFont.truetype(font_path, size=60)
    except Exception:
        font = ImageFont.load_default()

    full_name = f"{registration.name.upper()} {registration.first_name}"
    text_bbox = draw.textbbox((0, 0), full_name, font=font)
    text_width = text_bbox[2] - text_bbox[0]

    name_font_size = 60
    while text_width > max_width and name_font_size > 10:
        name_font_size -= 5
        try:
            font = ImageFont.truetype(font_path, size=name_font_size)
        except Exception:
            font = ImageFont.load_default()
        text_bbox = draw.textbbox((0, 0), full_name, font=font)
        text_width = text_bbox[2] - text_bbox[0]

    text_position = (
        badge_img.width // 2 - text_width // 2,
        850,
    )
    draw.text(text_position, full_name, fill="white", font=font)

    statut_font_size = 140
    try:
        font_statut = ImageFont.truetype(font_path, size=statut_font_size)
    except Exception:
        font_statut = ImageFont.load_default()

    try:
        font_societe = ImageFont.truetype(font_path, size=40)
    except Exception:
        font_societe = ImageFont.load_default()

    statut_part1 = registration.id_type.name_fr
    letter_spacing = 30
    letters = list(statut_part1)
    total_width = 0
    letter_positions = []

    for letter in letters:
        bbox = draw.textbbox((0, 0), letter, font=font_statut)
        letter_width = bbox[2] - bbox[0]
        letter_positions.append((letter, total_width))
        total_width += letter_width + letter_spacing

    while total_width > max_width and statut_font_size > 20:
        statut_font_size -= 10
        try:
            font_statut = ImageFont.truetype(font_path, size=statut_font_size)
        except Exception:
            font_statut = ImageFont.load_default()
        total_width = 0
        letter_positions = []
        for letter in letters:
            bbox = draw.textbbox((0, 0), letter, font=font_statut)
            letter_width = bbox[2] - bbox[0]
            letter_positions.append((letter, total_width))
            total_width += letter_width + letter_spacing

    while total_width > max_width and letter_spacing > 5:
        letter_spacing -= 5
        total_width = 0
        letter_positions = []
        for letter in letters:
            bbox = draw.textbbox((0, 0), letter, font=font_statut)
            letter_width = bbox[2] - bbox[0]
            letter_positions.append((letter, total_width))
            total_width += letter_width + letter_spacing

    start_x = badge_img.width // 2 - total_width // 2
    for letter, offset in letter_positions:
        draw.text((start_x + offset, 1450), letter, fill="white", font=font_statut)

    societe_font_size = 40
    statut_part2 = (
        registration.name_organization
        if registration.name_organization
        else "Universite"
    )
    statut_bbox2 = draw.textbbox((0, 0), statut_part2, font=font_societe)
    statut_width2 = statut_bbox2[2] - statut_bbox2[0]

    while statut_width2 > max_width and societe_font_size > 10:
        societe_font_size -= 5
        try:
            font_societe = ImageFont.truetype(font_path, size=societe_font_size)
        except Exception:
            font_societe = ImageFont.load_default()
        statut_bbox2 = draw.textbbox((0, 0), statut_part2, font=font_societe)
        statut_width2 = statut_bbox2[2] - statut_bbox2[0]

    statut_position2 = (
        badge_img.width // 2 - statut_width2 // 2,
        1650,
    )
    draw.text(statut_position2, statut_part2, fill="white", font=font_societe)

    buffer = BytesIO()
    badge_img.save(buffer, format="PNG", quality=100, dpi=(300, 300))
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


def home(request):
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
