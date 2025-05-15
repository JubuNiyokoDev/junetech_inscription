from django.db import models
import uuid
from django.conf import settings
from datetime import datetime


class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    date_naissance = models.DateField()
    numero_telephone = models.CharField(max_length=15)
    date_inscription = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=False)  # Admin validation

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    class Meta:
        verbose_name = "Participant"
        verbose_name_plural = "Participants"


class Scan(models.Model):
    TYPE_SCAN_CHOICES = [
        ("ENTREE", "Entrée"),
        ("SORTIE", "Sortie"),
    ]

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="scans"
    )
    type_scan = models.CharField(max_length=10, choices=TYPE_SCAN_CHOICES)
    date_scan = models.DateTimeField(auto_now_add=True)
    jour_evenement = models.PositiveIntegerField(editable=False)

    def save(self, *args, **kwargs):
        event_start_date = getattr(
            settings, "EVENT_START_DATE", datetime(2025, 6, 1).date()
        )
        self.jour_evenement = max(
            1, (self.date_scan.date() - event_start_date).days + 1
        )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Scan"
        verbose_name_plural = "Scans"
        unique_together = ("participant", "type_scan", "jour_evenement")

    def __str__(self):
        return f"{self.participant} - {self.type_scan} - Jour {self.jour_evenement}"
