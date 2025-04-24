from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Cita
from patient.models import PatientProfile
import datetime

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo Electrónico')
    name = forms.CharField(required=True, label='Nombre')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')  # Correct field names

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            PatientProfile.objects.create(user=user, name=self.cleaned_data['name'])
        return user

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ('name', 'profile_picture')


class CitaForm(forms.ModelForm):
    hora = forms.ChoiceField(choices=[], label='Hora')

    class Meta:
        model = Cita
        fields = ['servicio', 'fecha', 'hora']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(CitaForm, self).__init__(*args, **kwargs)

        # Generar horas válidas de 9:00–13:00 y 15:00–20:00 en intervalos de 30 minutos
        HORAS_VALIDAS = [
            (datetime.time(h, m).strftime('%H:%M'), datetime.time(h, m).strftime('%H:%M'))
            for h in list(range(9, 13)) + list(range(15, 20))
            for m in (0, 30)
        ]
        self.fields['hora'].choices = HORAS_VALIDAS

    def clean_hora(self):
        hora_str = self.cleaned_data['hora']
        hora_obj = datetime.datetime.strptime(hora_str, '%H:%M').time()
        if not ((datetime.time(9, 0) <= hora_obj < datetime.time(13, 0)) or
                (datetime.time(15, 0) <= hora_obj < datetime.time(20, 0))):
            raise forms.ValidationError("La hora debe estar entre 9:00–13:00 o 15:00–20:00")
        return hora_str