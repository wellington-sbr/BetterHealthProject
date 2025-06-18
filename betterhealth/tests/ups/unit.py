from django.test import TestCase
from django.contrib.auth.models import User
from betterhealth.models import Service, PatientProfile, Cita
from betterhealth.api_client import MutuaApiClient
from decimal import Decimal

class ServiceModelTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(
            name="Test Service",
            description="Test Description",
            service_type="Consultation",
            price=Decimal('50.00'),
            included_in_mutual=True,
            duration_minutes=30,
            requires_mutual_authorization=False
        )

    def test_service_creation(self):
        self.assertEqual(self.service.name, "Test Service")
        self.assertEqual(self.service.price, Decimal('50.00'))
        self.assertTrue(self.service.included_in_mutual)

class PatientProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = PatientProfile.objects.create(
            user=self.user,
            name="Test Patient",
            tiene_mutua=True,
            numero_poliza="12345"
        )

    def test_profile_creation(self):
        self.assertEqual(self.profile.name, "Test Patient")
        self.assertEqual(self.profile.email, self.user.email)
        self.assertTrue(self.profile.tiene_mutua)

class MutuaApiClientIntegrationTest(TestCase):
    def test_get_servicios_mutua_returns_data(self):
        client = MutuaApiClient()
        response = client.get_servicios_mutua()
        print("API response:", response)
        self.assertTrue(response.get("success"))
        self.assertIn("data", response)