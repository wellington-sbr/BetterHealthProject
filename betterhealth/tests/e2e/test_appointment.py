import pytest
from playwright.sync_api import Page, expect
from betterhealth.models import Service, PatientProfile
import datetime
from betterhealth.models import Cita
from betterhealth.models import StaffProfile
import datetime
from betterhealth.models import Service, PatientProfile, Cita

@pytest.mark.django_db
class TestAppointmentEndToEnd:
    def setup_service_and_patient(self, django_user_model):
        service = Service.objects.create(
            name="Consulta Especialista",
            description="Consulta con especialista",
            service_type="especialista",
            price=80,
            included_in_mutual=False,
            duration_minutes=45,
            requires_mutual_authorization=False,
        )
        patient_user = django_user_model.objects.create_user(username="apptester", password="TestPass456!")
        PatientProfile.objects.create(user=patient_user, name="Paciente E2E")
        return service, patient_user

    def login_patient(self, page: Page, live_server):
        page.goto(f"{live_server.url}/login/")
        page.fill('input[name="username"]', "apptester")
        page.fill('input[name="password"]', "TestPass456!")
        page.click('button[type="submit"]')

    def test_patient_full_appointment_flow(self, page: Page, live_server, django_user_model):
        service, patient_user = self.setup_service_and_patient(django_user_model)
        self.login_patient(page, live_server)
        # Schedule appointment
        page.goto(f"{live_server.url}/programar-cita/")
        page.select_option('select[name="servicio"]', label="Consulta Especialista")
        # Find next weekday
        today = datetime.date.today()
        for i in range(1, 8):
            d = today + datetime.timedelta(days=i)
            if d.weekday() < 5:
                valid_date = d
                break
        page.fill('input[name="fecha"]', valid_date.strftime("%Y-%m-%d"))
        page.select_option('select[name="hora"]', index=0)
        page.click('button[type="submit"]')
        expect(page.locator("body")).to_contain_text("se guardó correctamente")
        # Go to "Mis Citas"
        page.goto(f"{live_server.url}/mis-citas/")
        expect(page.locator(".appointment-card")).to_contain_text("Consulta Especialista")
        # View details
        page.click(".appointment-card")
        expect(page.locator("body")).to_contain_text("Detalles de la Cita")
        # Re-schedule
        page.click("#reschedule-button")
        # Pick another valid date
        for i in range(2, 9):
            d = today + datetime.timedelta(days=i)
            if d.weekday() < 5:
                new_date = d
                break
        page.fill('input[name="fecha"]', new_date.strftime("%Y-%m-%d"))
        page.select_option('select[name="hora"]', index=1)
        page.click("#confirm-reschedule")
        expect(page.locator("body")).to_contain_text("Mis Citas")
        # Cancel appointment
        page.goto(f"{live_server.url}/mis-citas/")
        page.click(".appointment-card")
        page.click("#cancel-button")
        page.click("#confirm-cancel")
        expect(page.locator("body")).to_contain_text("Mis Citas")

    def setup_admin(self, django_user_model):
        admin_user = django_user_model.objects.create_user(username="adminappt", password="AdminPass456!")
        StaffProfile.objects.create(user=admin_user, name="Admin E2E", role="admin")
        return admin_user

    def login_admin(self, page: Page, live_server):
        page.goto(f"{live_server.url}/login/")
        page.fill('input[name="username"]', "adminappt")
        page.fill('input[name="password"]', "AdminPass456!")
        page.click('button[type="submit"]')

    def test_admin_can_confirm_and_cancel(self, page: Page, live_server, django_user_model):
        # Setup patient and appointment
        service = Service.objects.create(
            name="Consulta Especialista",
            description="Consulta con especialista",
            service_type="especialista",
            price=80,
            included_in_mutual=False,
            duration_minutes=45,
            requires_mutual_authorization=False,
        )
        patient_user = django_user_model.objects.create_user(username="apptester", password="TestPass456!")
        PatientProfile.objects.create(user=patient_user, name="Paciente E2E")
        cita = Cita.objects.create(
            usuario=patient_user,
            servicio=service,
            fecha=datetime.date.today(),
            hora=datetime.time(10, 0),
            estado="pendiente"
        )
        # Setup admin
        self.setup_admin(django_user_model)
        self.login_admin(page, live_server)
        # Go to admin panel
        page.goto(f"{live_server.url}/admin-panel/")
        expect(page.locator("table")).to_contain_text("Consulta Especialista")
        # Confirm appointment
        page.click('a.btn-primary')
        expect(page.locator("body")).to_contain_text("Detalles de la Cita")
        page.click("#confirmation-button")
        page.click("#confirm-confirmation")
        expect(page.locator("body")).to_contain_text("Detalles de la Cita")
        # Cancel appointment
        page.click("#cancel-button")
        page.click("#confirm-cancel")
        expect(page.locator("body")).to_contain_text("Panel Administrativo")