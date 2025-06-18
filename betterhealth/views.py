import uuid
import csv
import io
from datetime import timezone, datetime, timedelta, time
from django.utils import timezone
from decimal import Decimal
from django.db.models import Count, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from .api_client import MutuaApiClient
from .forms import PatientProfileForm, CustomUserCreationForm, CitaForm, StaffCreationForm, ReprogramarCitaForm, CSVUploadForm, ServiceForm
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.utils.dateparse import parse_date
from .models import PatientProfile, Cita, Service, StaffProfile, Invoice
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .utils import verificar_mutua_paciente
from django.db import IntegrityError


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

@login_required
def finances_panel(request):
    """
    Panel de Finanzas para visualizar estadísticas y transacciones.
    """
    # Verificar permisos del usuario
    try:
        profile = StaffProfile.objects.get(user=request.user)
        if profile.role != 'finanzas':
            messages.error(request, "No tienes permisos para acceder a esta sección.")
            return redirect('home')
    except StaffProfile.DoesNotExist:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('home')

    # Aplicar filtros desde la solicitud
    servicio_filter = request.GET.get('servicio', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    estado = request.GET.get('estado', '')

    # Consulta base de citas
    citas_query = Cita.objects.select_related('servicio').all()

    # Aplicar filtros
    if servicio_filter:
        citas_query = citas_query.filter(servicio__name=servicio_filter)

    if fecha_inicio:
        citas_query = citas_query.filter(fecha__gte=fecha_inicio)

    if fecha_fin:
        citas_query = citas_query.filter(fecha__lte=fecha_fin)

    if estado:
        citas_query = citas_query.filter(estado=estado)

    # Calcular estadísticas
    estadisticas = {
        'citas_por_servicio': list(Cita.objects.values('servicio__name').annotate(total=Count('id')).order_by('-total')),
        'total_citas': Cita.objects.count(),
        'citas_ultimo_mes': Cita.objects.filter(fecha__gte=datetime.now(timezone.utc).replace(day=1)).count()
    }

    # Calcular ingresos estimados dinámicamente desde la base de datos
    ingresos_totales = citas_query.aggregate(total_ingresos=Sum('servicio__price'))['total_ingresos'] or 0
    ingresos_totales *= Decimal("1.21")  # Aplicar IVA del 21%

    estadisticas['ingresos_estimados'] = ingresos_totales

    # Obtener lista de servicios dinámicamente
    servicios = list(Service.objects.values_list('name', flat=True))

    # Paginar resultados (10 citas por página)
    paginator = Paginator(citas_query.order_by('-fecha'), 10)
    page = request.GET.get('page', 1)
    citas = paginator.get_page(page)

    context = {
        'estadisticas': estadisticas,
        'citas': citas,
        'servicios': servicios
    }

    return render(request, 'financial/panel_finanzas.html', context)

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

def boss_only(user):
    return user.is_authenticated and user.username == "boss"

@user_passes_test(boss_only)
def register_staff(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Nuevo miembro del personal registrado.")
            if form.cleaned_data['role'] == 'admin':
                return redirect('panel_administrativo')
            else:
                return redirect('panel_finanzas')
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
            tiene_mutua = request.POST.get('tiene_mutua') == 'on'
            numero_poliza = request.POST.get('numero_poliza', '').strip()
            nombre_usuario = form.cleaned_data.get('username', '').strip()

            if tiene_mutua and numero_poliza:
                try:
                    verificacion = verificar_mutua_paciente(numero_poliza, nombre_usuario)
                    if not verificacion['valido']:
                        messages.error(request, verificacion['error'] or 'Verificación fallida')
                        return render(request, 'patient/register.html', {'form': form})
                except Exception as e:
                    messages.error(request, 'Error al verificar la mutua')
                    return render(request, 'patient/register.html', {'form': form})

            # SEGUNDO: Solo crear usuario si todo está bien
            user = form.save()

            # TERCERO: Crear o actualizar perfil
            profile, created = PatientProfile.objects.get_or_create(user=user)
            profile.name = user.username
            profile.tiene_mutua = tiene_mutua
            profile.numero_poliza = numero_poliza if tiene_mutua else ''

            # Si la mutua fue verificada, guardar datos
            if tiene_mutua and numero_poliza:
                try:
                    # Ya sabemos que es válida porque la verificamos arriba
                    verificacion = verificar_mutua_paciente(numero_poliza)
                    profile.mutua_verificada = True
                    profile.datos_mutua = verificacion.get('datos', {})
                except Exception:
                    profile.mutua_verificada = False

            profile.dni = request.POST.get('dni', '').strip()
            profile.save()

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
                elif staff.role == 'finanzas':
                    return redirect('panel_finanzas')
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

        return render(request, 'patient/profile.html', {'profile': profile})


@login_required
def appointments_view(request):
    return render(request, 'patient/appointments.html')


@login_required
def settings_view(request):
    return render(request, 'patient/settings.html')


def contact_view(request):
    return render(request, 'patient/contact.html')



def get_precise_available_slots(servicio_id, fecha):
    """
    Devuelve una lista de horarios disponibles (como '%H:%M') en los que se puede agendar
    un servicio con duración arbitraria, sin romper bloques ni desperdiciar tiempo.
    """
    servicio = get_object_or_404(Service, id=servicio_id)
    duracion = timedelta(minutes=servicio.duration_minutes)

    # Horarios de la clínica: 9:00-12:30 y 15:00-19:30
    horarios_clinica = []

    # Mañana: 9:00 - 12:30
    inicio_manana = datetime.combine(fecha, time(9, 0))
    fin_manana = datetime.combine(fecha, time(12, 30))
    horarios_clinica.append((inicio_manana, fin_manana))

    # Tarde: 15:00 - 19:30
    inicio_tarde = datetime.combine(fecha, time(15, 0))
    fin_tarde = datetime.combine(fecha, time(19, 30))
    horarios_clinica.append((inicio_tarde, fin_tarde))

    # Obtener todas las citas del día (no solo del mismo servicio)
    citas = Cita.objects.filter(
        fecha=fecha,
        estado__in=['pendiente', 'confirmado']
    ).select_related('servicio').order_by('hora')

    # Convertir citas en bloques ocupados
    bloques_ocupados = []
    for cita in citas:
        inicio = datetime.combine(fecha, cita.hora)
        fin = inicio + timedelta(minutes=cita.servicio.duration_minutes)
        bloques_ocupados.append((inicio, fin))

    disponibles = []

    # Revisar cada período de horario de la clínica
    for inicio_periodo, fin_periodo in horarios_clinica:
        # Filtrar bloques ocupados que están en este período
        bloques_en_periodo = [
            (max(inicio, inicio_periodo), min(fin, fin_periodo))
            for inicio, fin in bloques_ocupados
            if inicio < fin_periodo and fin > inicio_periodo
        ]

        # Ordenar bloques por hora de inicio
        bloques_en_periodo.sort()

        # Agregar un bloque al final para simplificar el algoritmo
        bloques_en_periodo.append((fin_periodo, fin_periodo))

        # Buscar huecos libres
        actual = inicio_periodo

        for inicio_ocupado, fin_ocupado in bloques_en_periodo:
            # Buscar slots disponibles entre actual y inicio_ocupado
            while actual + duracion <= inicio_ocupado:
                disponibles.append(actual.strftime('%H:%M'))
                actual += timedelta(minutes=30)  # Avanzar en bloques de 30 min

            # Mover actual al final del bloque ocupado
            actual = max(actual, fin_ocupado)

    return disponibles


def get_all_possible_slots():
    """
    Devuelve todos los slots posibles de la clínica en formato HH:MM
    """
    slots = []

    # Mañana: 9:00 - 12:30
    for h in range(9, 13):
        for m in [0, 30]:
            if h == 12 and m > 30:
                break
            slots.append(f"{h:02d}:{m:02d}")

    # Tarde: 15:00 - 19:30
    for h in range(15, 20):
        for m in [0, 30]:
            if h == 19 and m > 30:
                break
            slots.append(f"{h:02d}:{m:02d}")

    return slots


@require_GET
def get_horarios_disponibles(request):
    """
    Vista AJAX que devuelve los horarios disponibles para un servicio y fecha específicos
    """
    servicio_id = request.GET.get('servicio')
    fecha_str = request.GET.get('fecha')

    if not servicio_id or not fecha_str:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    try:
        servicio = Service.objects.get(id=servicio_id)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except (Service.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Parámetros inválidos'}, status=400)

    # Obtener horarios disponibles usando tu función existente
    horarios_disponibles = get_precise_available_slots(servicio_id, fecha)

    # Obtener todos los slots posibles
    todos_los_slots = get_all_possible_slots()

    # Los ocupados son todos los que no están disponibles
    horarios_ocupados = [slot for slot in todos_los_slots if slot not in horarios_disponibles]

    return JsonResponse({
        'horarios': horarios_disponibles,
        'ocupados': horarios_ocupados
    })

@login_required
def programar_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.usuario = request.user

            if cita.fecha.weekday() in [5, 6]:
                messages.error(request, "Por favor, seleccione un día entre semana (lunes a viernes) para su cita.")
                return redirect('programar_cita')

            hora_str = form.cleaned_data['hora']
            cita.hora = datetime.strptime(hora_str, '%H:%M').time()

            horas_disponibles = get_precise_available_slots(cita.servicio.id, cita.fecha)
            if hora_str not in horas_disponibles:
                messages.error(request, "Este horario no está disponible. Por favor, seleccione otro.")
                return redirect('programar_cita')

            # Verificación de autorización por mutua
            try:
                profile = PatientProfile.objects.get(user=request.user)
                servicio = cita.servicio

                if servicio.requires_mutual_authorization:
                    if not profile.tiene_mutua or not profile.mutua_verificada:
                        messages.error(request, f"El servicio '{servicio.name}' requiere autorización de mutua, pero tu perfil no tiene una mutua verificada.")
                        return redirect('programar_cita')

                    if not servicio.included_in_mutual:
                        messages.error(request, f"El servicio '{servicio.name}' no está autorizado por la clínica para pacientes con mutua.")
                        return redirect('programar_cita')

                    cita.autorizado_mutua = True  # Aquí podrías agregar lógica para número de autorización si aplica

            except PatientProfile.DoesNotExist:
                messages.error(request, "No se encontró tu perfil de paciente.")
                return redirect('programar_cita')

            cita.save()
            return render(request, 'patient/cita_confirmacion.html', {'cita': cita})
    else:
        form = CitaForm()

    return render(request, 'patient/programar_cita.html', {'form': form})

from django.http import JsonResponse
from .models import Service, PatientProfile
from .utils import verificar_mutua_paciente

@login_required
def verificar_autorizacion_servicio(request):
    servicio_id = request.GET.get('servicio_id')
    try:
        servicio = Service.objects.get(id=servicio_id)
        profile = PatientProfile.objects.get(user=request.user)

        if not profile.tiene_mutua or not profile.mutua_verificada:
            return JsonResponse({'autorizado': False, 'mensaje': 'No tienes una mutua verificada.'})

        if not servicio.included_in_mutual or not servicio.requires_mutual_authorization:
            return JsonResponse({'autorizado': False, 'mensaje': f"El servicio '{servicio.name}' no está autorizado por la mutua."})

        return JsonResponse({'autorizado': True, 'mensaje': f"El servicio '{servicio.name}' está autorizado por la mutua."})
    except Service.DoesNotExist:
        return JsonResponse({'autorizado': False, 'mensaje': 'Servicio no encontrado.'})
    except PatientProfile.DoesNotExist:
        return JsonResponse({'autorizado': False, 'mensaje': 'Perfil de paciente no encontrado.'})



def mis_citas(request):
    citas = Cita.objects.all()
    servicio_input = request.GET.get('servicio')
    fecha = request.GET.get('fecha')
    servicio_invalido = False

    if servicio_input:
        # Verificamos si existe algún servicio que coincida
        if Service.objects.filter(name__icontains=servicio_input).exists():
            citas = citas.filter(servicio__name__icontains=servicio_input)
        else:
            citas = Cita.objects.none()
            # No hay coincidencias
            servicio_invalido = True

    if fecha:
        citas = citas.filter(fecha=fecha)

    return render(request, 'patient/mis_citas.html', {
        'citas': citas,
        'servicio_invalido': servicio_invalido
    })

def detalle_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    return render(request, 'patient/detalle_cita.html', {'cita': cita})

def detalle_cita_admin(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    return render(request, 'staff/detalles_cita_admin.html', {'cita': cita})


@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)

    if hasattr(request.user, 'staffprofile') or cita.usuario == request.user:
        cita.estado = 'cancelada'
        cita.save()

        messages.success(request, f"Tu cita para {cita.servicio.name} el {cita.fecha} ha sido cancelada correctamente.")
    else:
        messages.error(request, "No tienes permiso para cancelar esta cita.")

    return redirect('mis_citas')

@login_required
def confirmar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    if hasattr(request.user, 'staffprofile'):
        cita.estado = 'confirmado'
        cita.save()
        # Build invoice_data as in generar_factura or client_invoice_view
        return generar_factura(request, cita_id)
    return redirect('panel_administrativo')

@login_required
def reprogramar_cita(request, cita_id):
    """
    Permite a pacientes y personal reprogramar una cita, verificando disponibilidad.
    """
    cita = get_object_or_404(Cita, id=cita_id)

    if hasattr(request.user, 'staffprofile') or cita.usuario == request.user:
        if request.method == 'POST':
            form = CitaForm(horas_disponibles=[], horas_ocupadas=[])
            if form.is_valid():
                nueva_fecha = form.cleaned_data['fecha']
                nueva_hora = form.cleaned_data['hora']

                # Validar disponibilidad del nuevo horario
                horas_disponibles = get_precise_available_slots(cita.servicio.id, cita.fecha)
                if nueva_hora.strftime('%H:%M') not in horas_disponibles:
                    messages.error(request, "Este horario no está disponible. Seleccione otro.")
                    return redirect('reprogramar_cita', cita_id=cita.id)

                # Validar que la nueva fecha no es fin de semana
                if nueva_fecha.weekday() in [5, 6]:
                    messages.error(request, "No se pueden agendar citas en fin de semana.")
                    return redirect('reprogramar_cita', cita_id=cita.id)

                form.save()
                messages.success(request, f"Tu cita para {cita.servicio.name} ha sido reprogramada correctamente.")
                return redirect('detalle_cita', cita_id=cita.id)
        else:
            form = CitaForm(horas_disponibles=[], horas_ocupadas=[])

        return render(request, 'patient/reprogramar_cita.html', {'form': form, 'cita': cita})

    messages.error(request, "No tienes permiso para reprogramar esta cita.")
    return redirect('mis_citas')
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


@login_required
def generar_factura(request, cita_id):
    """
    Genera una factura para una cita específica.
    """
    cita = get_object_or_404(Cita, id=cita_id)

    # Verificar permisos - el usuario debe ser el paciente o un staff
    if not hasattr(request.user, 'staffprofile') and cita.usuario != request.user:
        messages.error(request, "No tienes permiso para ver esta factura.")
        return redirect('mis_citas')

    # Generar número de factura único
    fecha_actual = datetime.now(timezone.utc)
    numero_factura = f"INV-{fecha_actual.year}-{uuid.uuid4().hex[:6].upper()}"

    # Obtener información del paciente
    try:
        patient_profile = PatientProfile.objects.get(user=cita.usuario)
        nombre_paciente = patient_profile.name
        address = patient_profile.address or ""
        city = patient_profile.city or ""
        zip_code = patient_profile.zip_code or ""
        dni = patient_profile.dni or ""
    except PatientProfile.DoesNotExist:
        nombre_paciente = cita.usuario.username
        address = ""
        city = ""
        zip_code = ""
        dni = ""

    # Obtener el servicio y su precio de la base de datos
    servicio_obj = cita.servicio
    precio_base = servicio_obj.price
    iva = precio_base * Decimal("0.21")
    total = precio_base + iva

    # Verificar si el paciente tiene cobertura de mutua
    mutua_api = MutuaApiClient()
    tiene_mutua = False
    cobertura_mutua = None

    # Intentar verificar cobertura con la API de la mutua (si está disponible)
    try:
        # Usamos un ID ficticio para este ejemplo - en producción sería el ID real del paciente
        verificacion = mutua_api.verificar_pertenencia_mutua(str(cita.usuario.id))
        if verificacion.get('success') and verificacion.get('data', {}).get('pertenece', False):
            tiene_mutua = True
            cobertura_mutua = verificacion.get('data', {})
    except Exception as e:
        # Si hay error en la API, asumimos que no tiene cobertura
        print(f"Error al verificar mutua: {e}")

    # Si tiene mutua, aplicar descuento del 100%
    descuento_mutua = 0
    a_pagar = total
    if tiene_mutua:
        descuento_mutua = total
        a_pagar = 0

    # Crear contexto para la plantilla
    context = {
        'cita': cita,
        'invoice_data': {
            'number': numero_factura,
            'date': fecha_actual.strftime('%d/%m/%Y'),
            'status': 'PAGADO' if tiene_mutua else 'PENDIENTE',
            'client': {
                'name': nombre_paciente,
                'dni': dni,
                'address': address,
                'city': city,
                'zip': zip_code,
                'email': cita.usuario.email
            },
            'service': {
                'type': servicio_obj.name,
                'specialist': "Dr. Asignado",  # En producción sería el médico real
                'date': cita.fecha.strftime('%d/%m/%Y'),
                'time': cita.hora.strftime('%H:%M')
            },
            'items': [
                {
                    'description': servicio_obj.name,
                    'basePrice': f"{precio_base:.2f}".replace('.', ','),
                    'tax': f"{iva:.2f}".replace('.', ','),
                    'quantity': 1,
                    'total': f"{total:.2f}".replace('.', ',')
                }
            ],
            'totals': {
                'subtotal': f"{precio_base:.2f}".replace('.', ','),
                'tax': f"{iva:.2f}".replace('.', ','),
                'mutualDiscount': f"{descuento_mutua:.2f}".replace('.', ','),
                'total': f"{a_pagar:.2f}".replace('.', ',')
            },
            'notes': "Servicio prestado en las instalaciones de BetterHealth."
        },
        'profile': patient_profile if 'patient_profile' in locals() else None,
    }

    # Si tiene mutua, agregar info
    if tiene_mutua:
        context['invoice_data']['mutua'] = {
            'name': "Mutua Universal",  # En producción sería el nombre real de la mutua
            'affiliateNumber': f"MU-{cita.usuario.id}",  # En producción sería el número real
            'coverage': "Completa"
        }
        context['invoice_data']['notes'] += " Factura cubierta por mutua. Documento informativo."
    else:
        context['invoice_data']['mutua'] = None

    return render(request, 'financial/invoice_templates/client_invoice.html', context)


@login_required
def listado_facturas(request):
    """
    Muestra un listado de todas las facturas asociadas al usuario.
    """
    # Para staff, mostrar todas las facturas
    if hasattr(request.user, 'staffprofile'):
        citas = Cita.objects.all().order_by('-fecha')
    else:
        # Para pacientes, mostrar solo sus facturas
        citas = Cita.objects.filter(usuario=request.user).order_by('-fecha')

    return render(request, 'patient/listado_facturas.html', {'citas': citas})


@login_required
def descargar_factura(request, cita_id):
    """
    Genera un PDF de la factura para descarga (versión simulada, solo redirecciona a vista HTML)
    En una implementación real, aquí se generaría un PDF usando bibliotecas como WeasyPrint o ReportLab
    """
    messages.info(request,
                  "Descarga de facturas en PDF disponible próximamente. Por ahora puedes imprimir la factura desde el navegador.")
    return redirect('generar_factura', cita_id=cita_id)


@login_required()
def listado_facturas(request):
    # Filtrar las citas según los parámetros de la solicitud
    servicio = request.GET.get('servicio', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    estado = request.GET.get('estado', '')
    # Filtrar las citas
    citas = Cita.objects.all()
    if servicio:
        citas = citas.filter(servicio__icontains=servicio)
    if fecha_inicio:
        citas = citas.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        citas = citas.filter(fecha__lte=fecha_fin)
    if estado:
        citas = citas.filter(estado=estado)
    # Obtener estadísticas
    estadisticas = {
        'ingresos_estimados': citas.aggregate(Sum('importe'))['importe__sum'] or 0,
        'total_citas': citas.count(),
        'citas_ultimo_mes': citas.filter(fecha__month=datetime.now(timezone.utc).month).count(),
        'citas_por_servicio': citas.values('servicio').annotate(total=Sum('importe')).order_by('-total'),
    }
    # Renderizar la plantilla
    return render(request, 'patient/listado_facturas.html', {
        'citas': citas,
        'estadisticas': estadisticas,
        'servicios': Cita.objects.values_list('servicio', flat=True).distinct(),  # Obtener lista de servicios
    })

@user_passes_test(boss_only)
def import_services_view(request):
    services = Service.objects.all()

    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["csv_file"]
            decoded_file = csv_file.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            for row in reader:
                try:
                    # Check if the service already exists
                    service, created = Service.objects.get_or_create(
                        name=row['Servicio'],
                        defaults={
                            "description": row['Descripción'],
                            "service_type": row['Tipo de Servicio'],
                            "price": float(row['Precio (€)'].replace(',', '.')),
                            "included_in_mutual": row['Incluido en Mutua'].lower() == 'sí',
                            "duration_minutes": int(row['Duración (min)']),
                            "requires_mutual_authorization": row['Requiere autorización mutua'].lower() == 'sí',
                        }
                    )

                    if created:
                        messages.success(request, f"Servicio '{service.name}' añadido correctamente.")
                    else:
                        messages.info(request, f"Servicio '{service.name}' ya existe en la base de datos.")

                except ValueError as e:
                    messages.error(request, f"Error al procesar servicio '{row['Servicio']}': {e}")

            messages.success(request, "Los servicios se han importado exitosamente.")
            return redirect("import_services")

    else:
        form = CSVUploadForm()
        service_form = ServiceForm()

    return render(request, "staff/import_services.html", {
        "form": form,
        "service_form": service_form,
        "services": services
    })

@user_passes_test(boss_only)
def add_service_view(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Servicio añadido correctamente.")
            return redirect("import_services")
    return redirect("import_services")


@user_passes_test(boss_only)
def delete_service_view(request, service_id):
    service = Service.objects.get(id=service_id)
    service.delete()
    messages.success(request, "Servicio eliminado correctamente.")
    return redirect("import_services")

@user_passes_test(boss_only)
def export_services_csv(request):
    services = Service.objects.all()
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=services_catalog.csv"

    writer = csv.writer(response)
    writer.writerow(["Servicio", "Descripción", "Tipo de Servicio", "Precio (€)", "Incluido en Mutua", "Duración (min)",
                     "Requiere autorización mutua"])

    for service in services:
        writer.writerow([
            service.name,
            service.description,
            service.service_type,
            service.price,
            "Sí" if service.included_in_mutual else "No",
            service.duration_minutes,
            "Sí" if service.requires_mutual_authorization else "No"
        ])

    return response

def services_catalog(request):
    services_mutual = Service.objects.filter(included_in_mutual=True)
    services_clinic_only = Service.objects.filter(included_in_mutual=False)

    return render(request, "patient/programar_cita.html", {
        "services_mutual": services_mutual,
        "services_clinic_only": services_clinic_only
    })


def all_services(request):
    # Vista completa del catálogo de servicios
    search_query = request.GET.get('servicio', '')
    service_type = request.GET.get('tipo_servicio', '')

    servicios_mutual = Service.objects.filter(included_in_mutual=True)
    servicios_clinic = Service.objects.filter(included_in_mutual=False)

    if search_query:
        servicios_mutual = servicios_mutual.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(service_type__icontains=search_query))

        servicios_clinic = servicios_clinic.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(service_type__icontains=search_query))

    if service_type == 'mutual':
        servicios_clinic = Service.objects.none()
    elif service_type == 'private':
        servicios_mutual = Service.objects.none()

    return render(request, "patient/all_services.html", {
        "services_mutual": servicios_mutual,
        "services_clinic": servicios_clinic,
        "search_query": search_query,
        "selected_type": service_type,
    })

def client_invoice_view(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    profile = cita.usuario.patientprofile
    service = cita.servicio

    mutua = None
    mutua_covers_service = False
    mutua_authorized = False

    # Check if patient has mutua and service is included in mutua
    if profile.tiene_mutua and profile.numero_poliza and service.included_in_mutual:
        api_client = MutuaApiClient()
        mutua_resp = api_client.verificar_pertenencia_mutua(profile.numero_poliza)
        if mutua_resp.get('success') and mutua_resp.get('data'):
            mutua_data = mutua_resp['data']
            mutua = {
                "name": mutua_data.get("nombre", "Mutua Universal"),
                "affiliateNumber": profile.numero_poliza,
                "coverage": mutua_data.get("cobertura", "Completa"),
            }
            mutua_covers_service = True

            # If the service requires authorization, check it
            if service.requires_mutual_authorization:
                auth_resp = api_client.consultar_historial_autorizaciones(profile.id)
                if auth_resp.get('success') and auth_resp.get('data'):
                    for auth in auth_resp['data']:
                        if str(auth.get('servicio_id')) == str(service.id) and auth.get('autorizado'):
                            mutua_authorized = True
                            break
                else:
                    mutua_authorized = False
            else:
                mutua_authorized = True  # No authorization needed
        else:
            mutua = {
                "name": "Mutua Universal",
                "affiliateNumber": profile.numero_poliza,
                "coverage": "Desconocida",
            }
            mutua_covers_service = False
            mutua_authorized = False

    # Company info (hardcoded as per your request)
    company_info = {
        "address": "Calle Principal, 123",
        "city": "Madrid",
        "zip": "28001",
        "country": "España",
        "phone": "+34 91 123 45 67",
        "email": "facturacion@betterhealth.es",
        "cif": "B-12345678"
    }

    # Service info
    service_info = {
        "type": service.service_type,
        "date": cita.fecha.strftime("%d/%m/%Y"),
        "time": cita.hora.strftime("%H:%M"),
    }

    # Items
    items = [{
        "description": service.name,
        "basePrice": f"{service.price:.2f}",
        "tax": f"{(service.price * 0.21):.2f}",
        "quantity": 1,
        "total": f"{(service.price * 1.21):.2f}"
    }]

    subtotal = float(service.price)
    tax = subtotal * 0.21
    total = subtotal + tax

    # Mutua discount logic
    mutual_discount = total if (mutua_covers_service and mutua_authorized) else 0.0
    total_to_pay = 0.0 if (mutua_covers_service and mutua_authorized) else total

    invoice_data = {
        "number": f"INV-{timezone.now().year}-{cita.id:05d}",
        "date": timezone.now().strftime("%d/%m/%Y"),
        "status": "PAGADO" if mutual_discount else "PENDIENTE",
        "client": {
            "name": profile.name,
            "dni": profile.dni,
            "address": profile.address,
            "city": profile.city,
            "zip": profile.zip_code,
            "email": profile.email,
        },
        "service": service_info,
        "mutua": mutua if (mutua_covers_service and mutua_authorized) else None,
        "items": items,
        "totals": {
            "subtotal": f"{subtotal:.2f}",
            "tax": f"{tax:.2f}",
            "mutualDiscount": f"{mutual_discount:.2f}",
            "total": f"{total_to_pay:.2f}"
        },
        "notes": (
            "Servicio cubierto por Mutua. Factura emitida a efectos informativos."
            if (mutua_covers_service and mutua_authorized)
            else "Servicio prestado en las instalaciones de BetterHealth."
        ),
        "company": company_info
    }

    return render(request, "financial/invoice_templates/client_invoice.html", {
        "invoice_data": invoice_data
    })

@login_required
def staff_profile_view(request):
    staff = StaffProfile.objects.get(user=request.user)
    return render(request, 'staff_profile.html', {'staff': staff})