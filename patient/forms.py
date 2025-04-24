from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Cita, PatientProfile, StaffProfile

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
        staff_profile.role = self.cleaned_data['role']  # asegúrate de setear el rol
        if commit:
            staff_profile.save()
        return staff_profile


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