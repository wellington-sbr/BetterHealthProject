from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Cita
from patient.models import PatientProfile

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
    class Meta:
        model = Cita  # Vinculamos este formulario con el modelo Cita
        fields = ['servicio', 'fecha', 'hora']

        # Puedes personalizar los widgets si lo necesitas
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),  # Establecemos el tipo de campo para la fecha
            'hora': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),  # Establecemos el tipo para la hora
        }