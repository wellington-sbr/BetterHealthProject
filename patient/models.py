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

    class ServiceType(models.Model):
        name = models.CharField(max_length=100)
        description = models.TextField(blank=True)

        def __str__(self):
            return self.name

    class Service(models.Model):
        name = models.CharField(max_length=200)
        description = models.TextField()
        service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='services')
        price = models.DecimalField(max_digits=10, decimal_places=2)
        included_in_insurance = models.BooleanField(default=False)
        duration = models.IntegerField(help_text="Duration in minutes")
        requires_authorization = models.BooleanField(default=False)

        def __str__(self):
            return self.name

    class Appointment(models.Model):
        patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
        service = models.ForeignKey(Service, on_delete=models.CASCADE)
        date = models.DateField()
        start_time = models.TimeField()
        end_time = models.TimeField()
        created_at = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return f"{self.patient.username} - {self.service.name} - {self.date}"

    class ClinicSchedule(models.Model):
        """Para definir los horarios de la clínica"""
        DAY_CHOICES = [
            (0, 'Lunes'),
            (1, 'Martes'),
            (2, 'Miércoles'),
            (3, 'Jueves'),
            (4, 'Viernes'),
            (5, 'Sábado'),
            (6, 'Domingo'),
        ]

        day_of_week = models.IntegerField(choices=DAY_CHOICES)
        morning_start = models.TimeField(null=True, blank=True)
        morning_end = models.TimeField(null=True, blank=True)
        afternoon_start = models.TimeField(null=True, blank=True)
        afternoon_end = models.TimeField(null=True, blank=True)
        is_working_day = models.BooleanField(default=True)