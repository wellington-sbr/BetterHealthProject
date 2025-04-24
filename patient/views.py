from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from patient.forms import PatientProfileForm, CustomUserCreationForm, ReprogramarCitaForm
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


@login_required
def programar_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.usuario = request.user
            cita.save()

            return render(request, 'cita_confirmacion.html', {'cita': cita})
        else:
            # Si hay errores de validación en el formulario
            if 'fecha' in form.errors:
                # Buscar si el error está relacionado con fin de semana
                for error in form.errors.get('fecha', []):
                    if "Solo se permiten días de lunes a viernes" in error:
                        messages.error(request,
                                       'Por favor, seleccione un día entre semana (lunes a viernes) para su cita.')
                        break
            # También puedes manejar otros errores si es necesario
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


@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)

    if cita.usuario != request.user:
        messages.error(request, "No tienes permiso para cancelar esta cita.")
        return redirect('mis_citas')

    servicio = cita.servicio
    fecha = cita.fecha

    cita.delete()

    messages.success(request, f"Tu cita para {servicio} el día {fecha} ha sido cancelada correctamente.")

    return redirect('mis_citas')


@login_required
def reprogramar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)

    if cita.usuario != request.user:
        messages.error(request, "No tienes permiso para reprogramar esta cita.")
        return redirect('mis_citas')

    if request.method == 'POST':
        form = ReprogramarCitaForm(request.POST, instance=cita)
        if form.is_valid():
            form.save()
            messages.success(request, f"Tu cita para {cita.servicio} ha sido reprogramada correctamente.")
            return redirect('detalle_cita', cita_id=cita.id)
    else:
        form = ReprogramarCitaForm(instance=cita)

    return render(request, 'reprogramar_cita.html', {'form': form, 'cita': cita})