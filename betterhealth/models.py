from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    service_type = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    included_in_mutual = models.BooleanField()
    duration_minutes = models.IntegerField()
    requires_mutual_authorization = models.BooleanField()

    def __str__(self):
        return self.name

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
    servicio = models.ForeignKey(Service, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    importe = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=20, choices=[('pagado', 'Pagado'),('confirmado', 'Confirmado'), ('pendiente', 'Pendiente')], default='pendiente')

    def __str__(self):
        return f'Cita de {self.usuario.username} para {self.servicio.name} el {self.fecha} a las {self.hora}'

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

class Invoice(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    date = models.DateField()
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    mutua_discount = models.BooleanField(default=False)

    def __str__(self):
        return f"Factura de {self.patient.name} para {self.cita.servicio.name} el {self.date} con un importe de {self.total}"
