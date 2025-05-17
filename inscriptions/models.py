from django.db import models
import uuid
from django.conf import settings
from datetime import datetime
import random
import string


class TypeEvent(models.Model):
    id_type_event = models.AutoField(primary_key=True)
    id_admin = models.UUIDField(default=uuid.uuid4, editable=False)
    name_fr = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    date_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name_fr

    class Meta:
        verbose_name = "Type d'Événement"
        verbose_name_plural = "Types d'Événement"


class Event(models.Model):
    id_event = models.AutoField(primary_key=True)
    id_admin = models.UUIDField(default=uuid.uuid4, editable=False)
    id_redactor = models.UUIDField(default=uuid.uuid4, editable=False)
    id_type_event = models.ForeignKey(
        TypeEvent, on_delete=models.CASCADE, related_name="events"
    )
    published = models.BooleanField(default=False)
    title_fr = models.CharField(max_length=200)
    text_fr = models.TextField()
    meta_name_fr = models.CharField(max_length=200)
    description_fr = models.TextField()
    title_en = models.CharField(max_length=200)
    text_en = models.TextField()
    meta_name_en = models.CharField(max_length=200)
    description_en = models.TextField()
    date_start_event = models.DateField()
    date_stop_event = models.DateField()
    localisation = models.CharField(max_length=200)
    date_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title_fr

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"


class RegistrationType(models.Model):
    id_type = models.AutoField(primary_key=True)
    id_admin = models.UUIDField(default=uuid.uuid4, editable=False)
    name_fr = models.CharField(
        max_length=50,
        choices=[
            ("PARTICULAR", "Particulier"),
            ("ONG", "ONG"),
            ("ENTREPRISE", "Entreprise"),
        ],
    )
    name_en = models.CharField(
        max_length=50,
        choices=[
            ("PARTICULAR", "Individual"),
            ("ONG", "NGO"),
            ("ENTREPRISE", "Company"),
        ],
    )
    date_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name_fr

    class Meta:
        verbose_name = "Type de Registration"
        verbose_name_plural = "Types de Registration"


class RegistrationVisitors(models.Model):
    id_registration = models.AutoField(primary_key=True)
    id_admin = models.UUIDField(default=uuid.uuid4, editable=False)
    id_redactor = models.UUIDField(default=uuid.uuid4, editable=False)
    id_event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="registrations"
    )
    validation = models.BooleanField(default=False)  # Admin validation
    id_type = models.ForeignKey(
        RegistrationType, on_delete=models.CASCADE, related_name="registrations"
    )
    name_organization = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=20)
    email = models.EmailField(max_length=50, unique=True)
    date_registration = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    registration_number = models.CharField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.registration_number:
            prefix = (
                self.first_name[:3].upper()
                if len(self.first_name) >= 3
                else self.first_name.upper()
            )
            suffix = "".join(random.choices(string.ascii_uppercase, k=3))
            self.registration_number = f"{prefix}{suffix}"
            while (
                RegistrationVisitors.objects.filter(
                    registration_number=self.registration_number
                )
                .exclude(id_registration=self.id_registration)
                .exists()
            ):
                suffix = "".join(random.choices(string.ascii_uppercase, k=3))
                self.registration_number = f"{prefix}{suffix}"
        if self.validation and not self.date_validation:
            self.date_validation = datetime.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.name} ({self.registration_number})"

    class Meta:
        verbose_name = "Registration Visiteur"
        verbose_name_plural = "Registrations Visiteurs"


class ImgRegistration(models.Model):
    id_img_registration = models.AutoField(primary_key=True)
    registration_number = models.ForeignKey(
        RegistrationVisitors,
        on_delete=models.CASCADE,
        related_name="images",
        to_field="registration_number",
    )
    url_img = models.CharField(max_length=255)
    date_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.registration_number}"

    class Meta:
        verbose_name = "Image de Registration"
        verbose_name_plural = "Images de Registration"


class Scan(models.Model):
    TYPE_SCAN_CHOICES = [
        ("ENTREE", "Entrée"),
        ("SORTIE", "Sortie"),
    ]

    registration = models.ForeignKey(
        RegistrationVisitors,
        on_delete=models.CASCADE,
        related_name="scans",
        to_field="registration_number",
    )
    type_scan = models.CharField(max_length=10, choices=TYPE_SCAN_CHOICES)
    date_scan = models.DateTimeField(auto_now_add=True)
    jour_evenement = models.PositiveIntegerField(editable=False)

    def save(self, *args, **kwargs):
        event_start_date = self.registration.id_event.date_start_event
        # S'assurer que date_scan est défini
        scan_date = self.date_scan or datetime.now()
        self.jour_evenement = max(1, (scan_date.date() - event_start_date).days + 1)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Scan"
        verbose_name_plural = "Scans"
        unique_together = ("registration", "type_scan", "jour_evenement")

    def __str__(self):
        return f"{self.registration} - {self.type_scan} - Jour {self.jour_evenement}"
