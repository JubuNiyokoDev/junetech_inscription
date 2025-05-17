from rest_framework import serializers
from .models import RegistrationVisitors, Scan
from django.core.validators import RegexValidator
from django.conf import settings
from datetime import datetime


class RegistrationVisitorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationVisitors
        fields = [
            "id_registration",
            "id_event",
            "id_type",
            "name_organization",
            "name",
            "first_name",
            "email",
            "date_registration",
        ]
        read_only_fields = ["id_registration", "date_registration"]

    def validate_email(self, value):
        if RegistrationVisitors.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà enregistré.")
        return value


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = ["id", "registration", "type_scan", "date_scan", "jour_evenement"]
        read_only_fields = ["id", "date_scan", "jour_evenement"]

    def validate(self, data):
        registration = data["registration"]
        type_scan = data["type_scan"]
        if not registration.id_event or not registration.id_event.date_start_event:
            raise serializers.ValidationError(
                "L'événement associé au visiteur est invalide ou n'a pas de date de début."
            )
        jour_evenement = max(
            1,
            (datetime.now().date() - registration.id_event.date_start_event).days + 1,
        )
        if Scan.objects.filter(
            registration=registration,
            type_scan=type_scan,
            jour_evenement=jour_evenement,
        ).exists():
            raise serializers.ValidationError(
                f"Ce visiteur a déjà un scan de type {type_scan} pour ce jour."
            )
        return data
