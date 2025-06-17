from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Cita, PatientProfile, StaffProfile, Service
import datetime

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "description", "service_type", "price", "included_in_mutual", "duration_minutes", "requires_mutual_authorization"]

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Subir archivo CSV")

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo Electrónico')
    name = forms.CharField(required=True, label='Nombre')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            PatientProfile.objects.create(user=user, name=self.cleaned_data['name'])
        return user

class StaffCreationForm(forms.ModelForm):
    username = forms.CharField(label="Nombre de usuario")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    role = forms.ChoiceField(choices=StaffProfile.ROLES, label="Rol")

    class Meta:
        model = StaffProfile
        fields = ['name', 'profile_picture', 'role']  # role se repite, está bien

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
        )
        staff_profile = super().save(commit=False)
        staff_profile.user = user
        staff_profile.role = self.cleaned_data['role']
        if commit:
            staff_profile.save()
        return staff_profile


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

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if fecha.weekday() >= 5:
            raise forms.ValidationError("Solo se permiten días de lunes a viernes.")
        return fecha

class ReprogramarCitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['fecha', 'hora']

        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }
