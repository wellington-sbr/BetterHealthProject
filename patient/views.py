from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from patient.forms import PatientProfileForm, CustomUserCreationForm
from patient.models import PatientProfile
from .forms import CitaForm
from .models import Cita


def home(request):
    return render(request, 'home.html')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cuenta creada exitosamente.')
            return redirect('profile')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'¡Bienvenido/a, {user.username}!')
            return redirect('profile')
        else:
            messages.error(request, 'Credenciales incorrectas. Inténtalo de nuevo.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


@login_required
def profile_view(request):
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    if created:
        profile.name = request.user.username
        profile.save()

    if request.method == 'POST' and request.FILES.get('profile_picture'):
        profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        messages.success(request, 'Foto de perfil actualizada correctamente.')
        return redirect('profile')

    return render(request, 'profile.html', {'profile': profile})


@login_required
def appointments_view(request):
    return render(request, 'appointments.html')


@login_required
def settings_view(request):
    return render(request, 'settings.html')


def contact_view(request):
    return render(request, 'contact.html')


def programar_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.usuario = request.user  # Asumiendo que usas autenticación
            cita.save()

            # Agregar mensaje de éxito con los detalles de la cita
            messages.success(request,
                             f'Cita guardada correctamente: {cita.fecha} a las {cita.hora} para el servicio {cita.servicio}.')

            # Redirigir a la página de mis citas
            return redirect(
                'programar_cita')  # Asegúrate de que 'mis_citas' sea el nombre correcto de tu URL de mis citas
    else:
        form = CitaForm()

    return render(request, 'programar_cita.html', {'form': form})


def mis_citas(request):
    citas = Cita.objects.all()

    # Filtrado por servicio
    servicio = request.GET.get('servicio')
    if servicio:
        citas = citas.filter(servicio__icontains=servicio)

    # Filtrado por fecha
    fecha = request.GET.get('fecha')
    if fecha:
        citas = citas.filter(fecha=fecha)

    return render(request, 'mis_citas.html', {'citas': citas})
def detalle_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    return render(request, 'detalle_cita.html', {'cita': cita})