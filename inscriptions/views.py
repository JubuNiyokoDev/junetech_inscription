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
from inscriptions.utils import validate_registration


def registration_badge_view(request, registration_number):
    img = get_object_or_404(ImgRegistration, registration_number=registration_number)
    return redirect(img.url_img)


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
