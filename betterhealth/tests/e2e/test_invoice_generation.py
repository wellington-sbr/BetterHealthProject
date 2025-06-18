import pytest
from playwright.sync_api import Page, expect
import datetime
from betterhealth.models import Service, PatientProfile, Cita, StaffProfile
from betterhealth.models import Cita

@pytest.mark.django_db
class TestInvoiceGeneration:
    def setup_service_and_patient(self, django_user_model):
        service = Service.objects.create(
            name="Consulta Factura",
            description="Consulta para pruebas de factura",
            service_type="especialista",
            price=100,
            included_in_mutual=False,
            duration_minutes=30,
            requires_mutual_authorization=False,
        )
        patient_user = django_user_model.objects.create_user(username="invoicepat", password="InvoicePass123!")
        PatientProfile.objects.create(user=patient_user, name="Paciente Factura")
        return service, patient_user

    def login_patient(self, page: Page, live_server):
        page.goto(f"{live_server.url}/login/")
        page.fill('input[name="username"]', "invoicepat")
        page.fill('input[name="password"]', "InvoicePass123!")
        page.click('button[type="submit"]')

    def setup_admin(self, django_user_model):
        admin_user = django_user_model.objects.create_user(username="admininv", password="AdminInv123!")
        StaffProfile.objects.create(user=admin_user, name="Admin Factura", role="admin")
        return admin_user

    def login_admin(self, page: Page, live_server):
        page.goto(f"{live_server.url}/login/")
        page.fill('input[name="username"]', "admininv")
        page.fill('input[name="password"]', "AdminInv123!")
        page.click('button[type="submit"]')

    def setup_financial(self, django_user_model):
        fin_user = django_user_model.objects.create_user(username="fininv", password="FinInv123!")
        StaffProfile.objects.create(user=fin_user, name="Finanzas Factura", role="finanzas")
        return fin_user

    def login_financial(self, page: Page, live_server):
        page.goto(f"{live_server.url}/login/")
        page.fill('input[name="username"]', "fininv")
        page.fill('input[name="password"]', "FinInv123!")
        page.click('button[type="submit"]')

    def test_invoice_generation_flow(self, page: Page, live_server, django_user_model):
        # Patient schedules appointment
        service, patient_user = self.setup_service_and_patient(django_user_model)
        self.login_patient(page, live_server)
        page.goto(f"{live_server.url}/programar-cita/")
        page.select_option('select[name="servicio"]', label="Consulta Factura")
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
        # Get cita id for later
        cita = Cita.objects.filter(usuario=patient_user, servicio=service).first()
        assert cita is not None

        # Admin confirms appointment
        self.setup_admin(django_user_model)
        self.login_admin(page, live_server)
        page.goto(f"{live_server.url}/admin-panel/")
        expect(page.locator("table")).to_contain_text("Consulta Factura")
        page.click(f'a[href="/detalle_cita_admin/{cita.id}/"]')
        expect(page.locator("body")).to_contain_text("Detalles de la Cita")
        page.click("#confirmation-button")
        page.click("#confirm-confirmation")
        expect(page.locator("body")).to_contain_text("FACTURA")
        expect(page.locator("#invoice-number")).to_be_visible()
        expect(page.locator("#invoice-status")).to_contain_text("PAGADO")  # or "PENDIENTE" depending on logic

        # Patient can see invoice in their list
        self.login_patient(page, live_server)
        page.goto(f"{live_server.url}/listado_facturas/")
        expect(page.locator(".factura-card")).to_contain_text("Consulta Factura")
        expect(page.locator(".factura-badge")).to_contain_text("CONFIRMADO")  # or "PAGADO"/"PENDIENTE"

        # Financial staff sees invoice in their list
        self.setup_financial(django_user_model)
        self.login_financial(page, live_server)
        page.goto(f"{live_server.url}/listado_facturas/")
        expect(page.locator(".factura-card")).to_contain_text("Consulta Factura")
        expect(page.locator(".factura-badge")).to_contain_text("CONFIRMADO")  # or "PAGADO"/"PENDIENTE"
        # Optionally, check invoice details
        page.click(".factura-card")
        expect(page.locator("body")).to_contain_text("Factura")