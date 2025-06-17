from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import time
from betterhealth.models import Service, Cita
from datetime import datetime, timedelta

class PerformanceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.service = Service.objects.create(
            name="Performance Test Service",
            price=50.00,
            duration_minutes=30
        )

    def test_appointment_list_load_time(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Create multiple appointments for testing
        for i in range(50):
            Cita.objects.create(
                usuario=self.user,
                servicio=self.service,
                fecha=datetime.now().date() + timedelta(days=i),
                hora='10:00',
                importe=50.00
            )

        start_time = time.time()
        response = self.client.get(reverse('mis_citas'))
        end_time = time.time()

        load_time = end_time - start_time
        self.assertLess(load_time, 1.0)  # Should load in less than 1 second
        self.assertEqual(response.status_code, 200)

    def test_service_search_performance(self):
        # Create multiple services
        for i in range(100):
            Service.objects.create(
                name=f"Test Service {i}",
                price=50.00,
                duration_minutes=30
            )

        start_time = time.time()
        response = self.client.get('/services/search/?q=Test')
        end_time = time.time()

        search_time = end_time - start_time
        self.assertLess(search_time, 0.5)  # Search should complete in less than 0.5 seconds