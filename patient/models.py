from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    @property
    def email(self):
        return self.user.email

class Cita(models.Model):
    servicio_choices = [
        ("Consulta médica general", "Consulta médica general"),
        ("Consulta de especialidad (Cardiología)", "Consulta de especialidad (Cardiología)"),
        ("Consulta de especialidad (Dermatología)", "Consulta de especialidad (Dermatología)"),
        ("Consulta de especialidad (Neurología)", "Consulta de especialidad (Neurología)"),
        ("Análisis de sangre completo", "Análisis de sangre completo"),
        ("Electrocardiograma (ECG)", "Electrocardiograma (ECG)"),
        ("Resonancia Magnética (RMN)", "Resonancia Magnética (RMN)"),
        ("Radiografía de tórax", "Radiografía de tórax"),
        ("Colonoscopia", "Colonoscopia"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Relación con el usuario
    servicio = models.CharField(max_length=255, choices=servicio_choices)
    fecha = models.DateField()
    hora = models.TimeField()

    def __str__(self):
        return f'Cita de {self.usuario.username} para {self.servicio} el {self.fecha} a las {self.hora}'

class StaffProfile(models.Model):
    ROLES = [
        ('admin', 'Administrativo'),
        ('finanzas', 'Finanzas'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES)
    name = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='staff_profiles/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"