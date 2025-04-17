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
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    servicio = models.CharField(max_length=100)

    def __str__(self):
        return f"Cita para {self.usuario} el {self.fecha} a las {self.hora}"