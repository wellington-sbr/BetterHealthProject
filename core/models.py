from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('financial', 'Finanzas'),
        ('paciente', 'Paciente')
    )
    role = models.CharField(max_length=10, choices=ROLES, default='paciente')

    # Añade campos adicionales si necesitas
    telefono = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

class Cita(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada')
    )
    paciente = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='citas_paciente')
    fecha_hora = models.DateTimeField()
    motivo = models.TextField()
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cita {self.id} - {self.paciente.get_full_name()}"