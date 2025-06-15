import uuid
import csv
import io
from datetime import timezone, datetime
from decimal import Decimal
from django.db.models import Count, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from .api_client import MutuaApiClient
from .forms import PatientProfileForm, CustomUserCreationForm, CitaForm, StaffCreationForm, ReprogramarCitaForm, CSVUploadForm, ServiceForm
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.utils.dateparse import parse_date
from .models import PatientProfile, Cita, Service, StaffProfile, Invoice

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

def register_staff(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Esto ya crea el User y el StaffProfile dentro del form
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
            user = form.save()

            # Solo crear perfil si no existe
            profile, created = PatientProfile.objects.get_or_create(user=user)
            profile.name = user.username
            profile.tiene_mutua = request.POST.get('tiene_mutua') == 'on'
            profile.numero_poliza = request.POST.get('numero_poliza', '').strip() if profile.tiene_mutua else ''
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


@login_required
def programar_cita(request):
    """
    Permite a los pacientes programar una nueva cita, asegurando disponibilidad de horario.
    """
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.usuario = request.user

            # Validar que el servicio tiene horarios disponibles
            horarios_disponibles = get_available_slots(cita.servicio.id, cita.fecha)
            if cita.hora.strftime('%H:%M') not in horarios_disponibles:
                messages.error(request, "Este horario no está disponible. Por favor, seleccione otro.")
                return redirect('programar_cita')

            # Validar que la fecha no es fin de semana
            if cita.fecha.weekday() in [5, 6]:  # 5 = Sábado, 6 = Domingo
                messages.error(request, "Por favor, seleccione un día entre semana (lunes a viernes) para su cita.")
                return redirect('programar_cita')

            cita.save()
            return render(request, 'patient/cita_confirmacion.html', {'cita': cita})
    else:
        form = CitaForm()

    return render(request, 'patient/programar_cita.html', {'form': form})

def get_available_slots(servicio_id, fecha):
    """
    Devuelve una lista de horarios disponibles para un servicio en una fecha específica.
    Excluye horarios ya reservados y permite reusar citas canceladas.
    """
    # Obtener la duración del servicio desde la base de datos
    servicio = get_object_or_404(Service, id=servicio_id)
    duracion = servicio.duration_minutes

    # Lista de horarios posibles en un día laboral (8:00 AM - 6:00 PM)
    horarios_disponibles = [f"{h}:00" for h in range(8, 18)]  # Horas completas

    # Buscar citas ya reservadas en esta fecha
    citas_ocupadas = Cita.objects.filter(servicio=servicio, fecha=fecha, estado__in=['pendiente', 'confirmado'])

    # Excluir horarios ocupados
    ocupados = [cita.hora.strftime('%H:%M') for cita in citas_ocupadas]
    horarios_libres = [hora for hora in horarios_disponibles if hora not in ocupados]

    return horarios_libres

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
        messages.success(request, f"La cita para {cita.servicio.name} el {cita.fecha} ha sido confirmada correctamente.")
        return render(request, 'financial/invoice_templates/client_invoice.html', {'cita': cita})

    return redirect('panel_administrativo')

@login_required
def reprogramar_cita(request, cita_id):
    """
    Permite a pacientes y personal reprogramar una cita, verificando disponibilidad.
    """
    cita = get_object_or_404(Cita, id=cita_id)

    if hasattr(request.user, 'staffprofile') or cita.usuario == request.user:
        if request.method == 'POST':
            form = ReprogramarCitaForm(request.POST, instance=cita)
            if form.is_valid():
                nueva_fecha = form.cleaned_data['fecha']
                nueva_hora = form.cleaned_data['hora']

                # Validar disponibilidad del nuevo horario
                horarios_disponibles = get_available_slots(cita.servicio.id, nueva_fecha)
                if nueva_hora.strftime('%H:%M') not in horarios_disponibles:
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
            form = ReprogramarCitaForm(instance=cita)

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
    except PatientProfile.DoesNotExist:
        nombre_paciente = cita.usuario.username

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
                'dni': "12345678Z",  # En producción sería el DNI real del paciente
                'address': "Dirección del paciente",  # En producción sería la dirección real
                'city': "Madrid",
                'zip': "28001",
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
        }
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

def add_service_view(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Servicio añadido correctamente.")
            return redirect("import_services")
    return redirect("import_services")


def delete_service_view(request, service_id):
    service = Service.objects.get(id=service_id)
    service.delete()
    messages.success(request, "Servicio eliminado correctamente.")
    return redirect("import_services")

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