from rest_framework import serializers
from .models import Participant, Scan
from django.core.validators import RegexValidator
from django.conf import settings
from datetime import datetime


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ["id", "nom", "prenom", "email", "date_naissance", "numero_telephone"]
        read_only_fields = ["id"]

    numero_telephone = serializers.CharField(
        validators=[
            RegexValidator(
                regex=r"^\+?[1-9]\d{1,14}$",
                message="Le numéro de téléphone doit être au format international (ex. : +1234567890).",
            )
        ]
    )

    def validate_email(self, value):
        if Participant.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà enregistré.")
        return value


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = ["participant", "type_scan", "date_scan", "jour_evenement"]
        read_only_fields = ["date_scan", "jour_evenement"]

    def validate(self, data):
        participant = data["participant"]
        type_scan = data["type_scan"]
        jour_evenement = max(
            1,
            (
                datetime.now().date()
                - getattr(settings, "EVENT_START_DATE", datetime(2025, 6, 1).date())
            ).days
            + 1,
        )
        if Scan.objects.filter(
            participant=participant, type_scan=type_scan, jour_evenement=jour_evenement
        ).exists():
            raise serializers.ValidationError(
                f"Ce participant a déjà un scan de type {type_scan} pour ce jour."
            )
        return data
