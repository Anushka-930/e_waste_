from django.test import TestCase


class SmokeTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_prediction_page_handles_post(self):
        payload = {
            'category': 'Printer',
            'device_type': 'Laser Printer',
            'weight_kg': '15.5',
            'condition': 'Good',
            'age_years': '3',
            'brand': 'Epson',
            'quantity': '2',
        }
        response = self.client.post('/predict/', payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Estimated Value')
