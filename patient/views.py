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

@login_required
def admin_panel(request):
    try:
        profile = StaffProfile.objects.get(user=request.user)
        if profile.role != 'administrative':
            messages.error(request, "No tienes permisos para acceder a esta sección.")
            return redirect('home')
    except StaffProfile.DoesNotExist:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('home')

    citas = Cita.objects.all()
    return render(request, 'panel_administrativo.html', {'citas': citas})


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

            # Verifica si el usuario tiene perfil de staff
            try:
                staff = StaffProfile.objects.get(user=user)
                if staff.role == 'administrative':
                    return redirect('panel_administrativo')
            except StaffProfile.DoesNotExist:
                pass

            return redirect('profile')  # Por defecto
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
        return render(request, 'staff_profile.html', {'profile': staff})
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

            # Pasa la cita como contexto a la plantilla de confirmación
            return render(request, 'cita_confirmacion.html', {'cita': cita})
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
def admin_calendar(request):
    return render(request, 'calendar_admin.html')

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

