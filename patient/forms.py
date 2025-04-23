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
        fields = ('username', 'email', 'Password', 'Password Confirmation')

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
        model = Cita
        fields = ['servicio', 'fecha', 'hora']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }