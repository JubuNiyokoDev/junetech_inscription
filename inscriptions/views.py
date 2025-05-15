from rest_framework import generics, views
from rest_framework.response import Response
from .models import Participant, Scan
from .serializers import ParticipantSerializer, ScanSerializer
from django.db.models import Count
from rest_framework.permissions import AllowAny
import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.urls import reverse
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from PIL import Image
import os


class ParticipantCreateView(generics.CreateAPIView):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        participant = serializer.save()
        context = {
            "prenom": participant.prenom,
            "nom": participant.nom,
        }
        email_html = render_to_string("email/confirmation_email.html", context)
        email = EmailMessage(
            subject="Confirmation de votre inscription à JuneTech 5ème Édition",
            body=email_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[participant.email],
        )
        email.content_subtype = "html"
        try:
            email.send()
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email : {e}")


class ParticipantDetailView(generics.RetrieveAPIView):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    lookup_field = "id"
    permission_classes = [AllowAny]


class ScanCreateView(generics.CreateAPIView):
    queryset = Scan.objects.all()
    serializer_class = ScanSerializer
    permission_classes = [AllowAny]


class ScanSummaryView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        jour_evenement = request.query_params.get("jour_evenement", None)
        filters = {}
        if jour_evenement:
            filters["jour_evenement"] = jour_evenement

        total_entrees = Scan.objects.filter(type_scan="ENTREE", **filters).count()
        total_sorties = Scan.objects.filter(type_scan="SORTIE", **filters).count()

        scans = Scan.objects.filter(**filters).select_related("participant")
        scan_list = [
            {
                "participant": f"{scan.participant.prenom} {scan.participant.nom}",
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


def generate_badge(request, id):
    participant = Participant.objects.get(id=id)
    if not participant.is_valid:
        return HttpResponse(status=403)

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(request.build_absolute_uri(reverse("participant-detail", args=[id])))
    qr.make(fit=True)
    qr_img = qr.make_image(fill="black", back_color="white")

    badge_path = os.path.join(settings.BASE_DIR, "static/images/badge_template.png")
    badge_img = Image.open(badge_path).convert("RGBA")
    qr_size = (150, 150)
    qr_img = qr_img.resize(qr_size, Image.Resampling.LANCZOS)
    qr_position = (100, 200)
    badge_img.paste(qr_img, qr_position, qr_img)

    buffer = BytesIO()
    badge_img.save(buffer, format="PNG")
    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response["Content-Disposition"] = (
        f"attachment; filename=badge_{participant.prenom}_{participant.nom}.png"
    )
    return response
