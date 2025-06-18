import pytest
from playwright.sync_api import Page, expect

@pytest.mark.django_db
class TestRegistration:
    def test_successful_registration(self, page: Page, live_server):
        page.goto(f"{live_server.url}/register/")
        page.fill('input[name="username"]', "testuser")
        page.fill('input[name="email"]', "testuser@example.com")
        page.fill('input[name="password1"]', "StrongPassword123!")
        page.fill('input[name="password2"]', "StrongPassword123!")
        page.check("#tiene_mutua")
        page.fill("#numero_poliza", "123456789")
        page.click('button[type="submit"]')
        expect(page).to_have_url(f"{live_server.url}/login/")
        expect(page.locator(".success-message")).to_contain_text("cuenta ha sido creada")

    def test_registration_validation_errors(self, page: Page, live_server):
        page.goto(f"{live_server.url}/register/")
        page.click('button[type="submit"]')
        expect(page.locator(".error-message")).to_contain_text("Este campo es obligatorio")
        page.fill('input[name="email"]', "notanemail")
        page.click('button[type="submit"]')
        expect(page.locator(".error-message")).to_contain_text("Introduzca una dirección de correo electrónico válida")

@pytest.mark.django_db
class TestAuthentication:
    def test_login_logout_flow(self, page: Page, live_server, django_user_model):
        django_user_model.objects.create_user(username="testuser", password="StrongPassword123!")
        page.goto(f"{live_server.url}/login/")
        page.fill('input[name="username"]', "testuser")
        page.fill('input[name="password"]', "StrongPassword123!")
        page.click('button[type="submit"]')
        expect(page.locator(".welcome-message")).to_contain_text("Bienvenido")
        page.click('a[href="/logout/"]')
        expect(page).to_have_url(f"{live_server.url}/login/")

@pytest.mark.django_db
class TestAccessControl:
    def test_protected_page_requires_login(self, page: Page, live_server):
        page.goto(f"{live_server.url}/dashboard/")
        expect(page).to_have_url(f"{live_server.url}/login/?next=/dashboard/")

    def test_logout_revokes_access(self, page: Page, live_server, django_user_model):
        django_user_model.objects.create_user(username="testuser", password="StrongPassword123!")
        page.goto(f"{live_server.url}/login/")
        page.fill('input[name="username"]', "testuser")
        page.fill('input[name="password"]', "StrongPassword123!")
        page.click('button[type="submit"]')
        page.click('a[href="/logout/"]')
        expect(page).to_have_url(f"{live_server.url}/login/")
        # Try to access a patient-only page
        page.goto(f"{live_server.url}/profile/")
        expect(page).to_have_url(f"{live_server.url}/login/?next=/profile/")

@pytest.mark.django_db
class TestStaffRegistrationAndAccess:
    def test_staff_registration_admin(self, page: Page, live_server):
        page.goto(f"{live_server.url}/register-staff/")
        page.fill('input[name="username"]', "adminuser")
        page.fill('input[name="password"]', "AdminPass123!")
        page.fill('input[name="name"]', "Admin Name")
        page.select_option('select[name="role"]', "admin")
        page.click('button[type="submit"]')
        # Should redirect to admin panel
        expect(page).to_have_url(f"{live_server.url}/admin-panel/")
        expect(page.locator("body")).to_contain_text("panel administrativo")

    def test_staff_registration_finanzas(self, page: Page, live_server):
        page.goto(f"{live_server.url}/register-staff/")
        page.fill('input[name="username"]', "finanzasuser")
        page.fill('input[name="password"]', "FinanzasPass123!")
        page.fill('input[name="name"]', "Finanzas Name")
        page.select_option('select[name="role"]', "finanzas")
        page.click('button[type="submit"]')
        # Should redirect to finances panel
        expect(page).to_have_url(f"{live_server.url}/panel-finanzas/")
        expect(page.locator("body")).to_contain_text("finanzas")

    def test_admin_access_control(self, page: Page, live_server, django_user_model):
        # Create a staff user with admin role
        from betterhealth.models import StaffProfile
        user = django_user_model.objects.create_user(username="adminuser", password="AdminPass123!")
        StaffProfile.objects.create(user=user, name="Admin Name", role="admin")
        page.goto(f"{live_server.url}/login/")
        page.fill('input[name="username"]', "adminuser")
        page.fill('input[name="password"]', "AdminPass123!")
        page.click('button[type="submit"]')
        expect(page).to_have_url(f"{live_server.url}/admin-panel/")
        expect(page.locator("body")).to_contain_text("panel administrativo")

    def test_finanzas_access_control(self, page: Page, live_server, django_user_model):
        # Create a staff user with finanzas role
        from betterhealth.models import StaffProfile
        user = django_user_model.objects.create_user(username="finanzasuser", password="FinanzasPass123!")
        StaffProfile.objects.create(user=user, name="Finanzas Name", role="finanzas")
        page.goto(f"{live_server.url}/login/")
        page.fill('input[name="username"]', "finanzasuser")
        page.fill('input[name="password"]', "FinanzasPass123!")
        page.click('button[type="submit"]')
        expect(page).to_have_url(f"{live_server.url}/panel-finanzas/")
        expect(page.locator("body")).to_contain_text("finanzas")