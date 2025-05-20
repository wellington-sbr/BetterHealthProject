from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from .forms import PatientProfileForm, CustomUserCreationForm, CitaForm, StaffCreationForm
from .models import PatientProfile, Cita, StaffProfile
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.http import HttpResponseForbidden
from betterhealth.forms import PatientProfileForm, CustomUserCreationForm, ReprogramarCitaForm
from betterhealth.models import PatientProfile
from .forms import CitaForm
from .models import Cita


@login_required
def admin_panel(request):
    try:
        profile = StaffProfile.objects.get(user=request.user)
        if profile.role != 'admin':
            messages.error(request, "No tienes permisos para acceder a esta sección.")
            return redirect('home')
    except StaffProfile.DoesNotExist:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('home')


    citas = Cita.objects.all()
    return render(request, 'staff/panel_administrativo.html', {'citas': citas})


def staff_required(role=None):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'staffprofile'):
                return HttpResponseForbidden("No tienes permiso para acceder a esta sección.")
            if role and request.user.staffprofile.role != role:
                return HttpResponseForbidden("Permisos insuficientes.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def register_staff(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Esto ya crea el User y el StaffProfile dentro del form
            messages.success(request, "Nuevo miembro del personal registrado.")
            return redirect('panel_administrativo')
    else:
        form = StaffCreationForm()
    return render(request, 'register_staff.html', {'form': form})

@login_required
def home(request):
    return render(request, 'patient/home.html')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cuenta creada exitosamente.')
            return redirect('home')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'patient/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'¡Bienvenido/a, {user.username}!')

            try:
                staff = StaffProfile.objects.get(user=user)
                if staff.role == 'admin':
                    return redirect('panel_administrativo')
                else:
                    return redirect('profile')
            except StaffProfile.DoesNotExist:
                return redirect('home')
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
    try:
        staff = StaffProfile.objects.get(user=request.user)
        return render(request, 'staff/templates/staff_profile.html', {'profile': staff})
    except StaffProfile.DoesNotExist:
        profile, created = PatientProfile.objects.get_or_create(user=request.user)
        if created:
            profile.name = request.user.username
            profile.save()

        if request.method == 'POST' and request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            messages.success(request, 'Foto de perfil actualizada correctamente.')
            return redirect('profile')

        return render(request, 'patient/profile.html', {'profile': profile})


@login_required
def appointments_view(request):
    return render(request, 'patient/appointments.html')


@login_required
def settings_view(request):
    return render(request, 'patient/settings.html')


def contact_view(request):
    return render(request, 'patient/contact.html')


@login_required
def programar_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.usuario = request.user
            cita.save()

            return render(request, 'patient/cita_confirmacion.html', {'cita': cita})
        else:
            if 'fecha' in form.errors:
                for error in form.errors.get('fecha', []):
                    if "Solo se permiten días de lunes a viernes" in error:
                        messages.error(request,
                                       'Por favor, seleccione un día entre semana (lunes a viernes) para su cita.')
                        break
    else:
        form = CitaForm()

    return render(request, 'patient/programar_cita.html', {'form': form})

def mis_citas(request):
    citas = Cita.objects.all()

    servicio = request.GET.get('servicio')
    if servicio:
        citas = citas.filter(servicio__icontains=servicio)

    fecha = request.GET.get('fecha')
    if fecha:
        citas = citas.filter(fecha=fecha)

    return render(request, 'patient/mis_citas.html', {'citas': citas})
def detalle_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    return render(request, 'patient/detalle_cita.html', {'cita': cita})


@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)

    try:
        profile = StaffProfile.objects.get(user=request.user)
        servicio = cita.servicio
        fecha = cita.fecha

        cita.delete()

        messages.success(request, f"Tu cita para {servicio} el día {fecha} ha sido cancelada correctamente.")

        return redirect('mis_citas')

    except StaffProfile.DoesNotExist:
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

    try:

        profile = StaffProfile.objects.get(user=request.user)
        if request.method == 'POST':
            form = ReprogramarCitaForm(request.POST, instance=cita)
            if form.is_valid():
                form.save()
                messages.success(request, f"Tu cita para {cita.servicio} ha sido reprogramada correctamente.")
                return redirect('detalle_cita', cita_id=cita.id)
        else:
            form = ReprogramarCitaForm(instance=cita)

        return render(request, 'patient/reprogramar_cita.html', {'form': form, 'cita': cita})

    except StaffProfile.DoesNotExist:
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

        return render(request, 'patient/reprogramar_cita.html', {'form': form, 'cita': cita})

@login_required
def admin_calendar(request):
    return render(request, 'staff/calendar_admin.html')

@login_required
def citas_json(request):
    start = request.GET.get('start')
    end = request.GET.get('end')

    citas = Cita.objects.filter(fecha__range=[start, end])
    eventos = []

    for cita in citas:
        eventos.append({
            "id": cita.id,
            "title": f"{cita.servicio} - {cita.usuario.username}",
            "start": cita.fecha.isoformat(),
            "url": reverse('detalle_cita', args=[cita.id])
        })

    return JsonResponse(eventos, safe=False)

