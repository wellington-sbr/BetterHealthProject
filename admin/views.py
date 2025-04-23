from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.generic import ListView
import json
from .mixins import AdminRequiredMixin
from core.models import Cita
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class AdminLoginView(LoginView):
    template_name = 'admin/login.html'
    redirect_authenticated_user = True

@login_required
class DashboardView(TemplateView):
    template_name = 'admin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Lógica para obtener citas del día
        return context

class AdminCalendarView(AdminRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = 'admin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fecha_actual = timezone.now().date()

        # Obtener citas y serializar a formato FullCalendar
        citas = Cita.objects.filter(fecha_hora__date=fecha_actual).values(
            'id', 'paciente__nombre', 'fecha_hora', 'motivo', 'estado'
        )

        # Convertir a formato de eventos para FullCalendar
        eventos = []
        for cita in citas:
            eventos.append({
                'title': f"{cita['paciente__nombre']} - {cita['motivo']}",
                'start': cita['fecha_hora'].isoformat(),
                'color': '#4CAF50' if cita['estado'] == 'confirmada' else '#D32F2F'
            })

        context.update({
            'fecha_actual': fecha_actual.strftime('%Y-%m-%d'),
            'eventos_json': json.dumps(eventos)
        })
        return context

class CalendarioView(LoginRequiredMixin, ListView):
    template_name = 'admin/calendario.html'
    model = Cita
    context_object_name = 'citas'

    def get_queryset(self):
        # Filtrar citas por mes/año según parámetros
        return super().get_queryset().filter(
            fecha_hora__month=self.kwargs.get('month')
        )