from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from appointments.models import Appointment
from doctors.models import Doctor
from patients.models import Patient
from users.models import User


class PrescriptionAPITests(APITestCase):
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@example.com',
            password='password123',
            is_verified=True
        )
        self.patient_user = User.objects.create_user(
            username='patient',
            email='patient@example.com',
            password='password123',
            is_verified=True
        )
        self.other_doctor_user = User.objects.create_user(
            username='otherdoctor',
            email='otherdoctor@example.com',
            password='password123',
            is_verified=True
        )

        self.doctor = Doctor.objects.create(user=self.doctor_user, status='approved')
        self.other_doctor = Doctor.objects.create(user=self.other_doctor_user, status='approved')
        self.patient = Patient.objects.create(user=self.patient_user)

        self.completed_appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            status=Appointment.Status.COMPLETED,
            date=timezone.now() - timedelta(days=1)
        )
        self.confirmed_appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            status=Appointment.Status.CONFIRMED,
            date=timezone.now()
        )

        self.valid_payload = {
            'appointment_id': self.completed_appointment.id,
            'diagnosis': 'Generalized anxiety symptoms',
            'notes': 'Review response after one week.',
            'medications': [
                {
                    'medication_name': 'Sertraline',
                    'dosage': '25 mg',
                    'frequency': 'Once daily',
                    'duration': '14 days',
                    'notes': 'Take after breakfast.'
                }
            ]
        }

    def test_doctor_can_create_prescription_for_completed_appointment(self):
        self.client.force_authenticate(user=self.doctor_user)

        response = self.client.post(
            reverse('doctor-prescription-create'),
            data=self.valid_payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['appointment_id'], self.completed_appointment.id)
        self.assertEqual(response.data['patient_id'], self.patient.id)
        self.assertEqual(len(response.data['medications']), 1)

    def test_patient_cannot_create_prescription(self):
        self.client.force_authenticate(user=self.patient_user)

        response = self.client.post(
            reverse('doctor-prescription-create'),
            data=self.valid_payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rejects_non_completed_appointment(self):
        self.client.force_authenticate(user=self.doctor_user)
        payload = {
            **self.valid_payload,
            'appointment_id': self.confirmed_appointment.id,
        }

        response = self.client.post(
            reverse('doctor-prescription-create'),
            data=payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('appointment_id', response.data)

    def test_rejects_duplicate_prescription_for_same_appointment(self):
        self.client.force_authenticate(user=self.doctor_user)
        first_response = self.client.post(
            reverse('doctor-prescription-create'),
            data=self.valid_payload,
            format='json'
        )
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        second_response = self.client.post(
            reverse('doctor-prescription-create'),
            data=self.valid_payload,
            format='json'
        )

        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('appointment_id', second_response.data)

    def test_patient_can_list_own_prescriptions(self):
        self.client.force_authenticate(user=self.doctor_user)
        create_response = self.client.post(
            reverse('doctor-prescription-create'),
            data=self.valid_payload,
            format='json'
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(reverse('patient-prescription-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], create_response.data['id'])
