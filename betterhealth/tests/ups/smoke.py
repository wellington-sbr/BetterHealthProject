from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from betterhealth.models import Service, PatientProfile

class SmokeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='smoketest',
            password='smoketest123'
        )
        self.service = Service.objects.create(
            name="Smoke Test Service",
            price=50.00,
            duration_minutes=30
        )

    def test_critical_paths(self):
        # Test Homepage Access
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        # Test User Login
        login_successful = self.client.login(
            username='smoketest',
            password='smoketest123'
        )
        self.assertTrue(login_successful)

        # Test Appointment Creation Page
        response = self.client.get(reverse('agendar_cita'))
        self.assertEqual(response.status_code, 200)

        # Test Profile Access
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_error_handling(self):
        # Test 404 Page
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)

        # Test Invalid Login
        response = self.client.post(reverse('login'), {
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)