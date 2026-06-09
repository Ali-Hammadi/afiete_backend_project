from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from doctors.models import Doctor
from users.models import User

from .models import SessionPrice


def create_doctor(username='doctor', email='doctor@example.com'):
    user = User.objects.create_user(
        username=username,
        email=email,
        password='test-pass-123',
    )
    doctor = Doctor.objects.create(user=user)
    return user, doctor


class SessionPriceModelTests(TestCase):
    def test_doctor_and_type_are_unique_together(self):
        _, doctor = create_doctor()
        SessionPrice.objects.create(
            doctor=doctor,
            type=SessionPrice.Type.Video,
            price=Decimal('50.00'),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SessionPrice.objects.create(
                    doctor=doctor,
                    type=SessionPrice.Type.Video,
                    price=Decimal('60.00'),
                )


class SessionPricesViewSetTests(APITestCase):
    url = '/api/appointmetns/dcotors/prices/'

    def setUp(self):
        self.user, self.doctor = create_doctor()
        self.other_user, self.other_doctor = create_doctor(
            username='other-doctor',
            email='other-doctor@example.com',
        )

    def test_post_creates_session_price_with_fixed_duration(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.url,
            {'type': 'video', 'price': '50.00', 'duration': 45},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session_price = SessionPrice.objects.get(doctor=self.doctor, type='video')
        self.assertEqual(session_price.duration, 30)
        self.assertEqual(session_price.price, Decimal('50.00'))
        self.assertEqual(response.data['duration'], 30)

    def test_post_rejects_duplicate_type_for_same_doctor(self):
        SessionPrice.objects.create(
            doctor=self.doctor,
            type='video',
            price=Decimal('50.00'),
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.url,
            {'type': 'video', 'price': '60.00'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Session type video already exists', str(response.data))

    def test_post_allows_same_type_for_different_doctors(self):
        SessionPrice.objects.create(
            doctor=self.doctor,
            type='video',
            price=Decimal('50.00'),
        )
        self.client.force_authenticate(self.other_user)

        response = self.client.post(
            self.url,
            {'type': 'video', 'price': '60.00'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            SessionPrice.objects.filter(
                doctor=self.other_doctor,
                type='video',
            ).exists()
        )

    def test_patch_updates_price_and_keeps_duration_fixed(self):
        SessionPrice.objects.create(
            doctor=self.doctor,
            duration=45,
            type='video',
            price=Decimal('50.00'),
        )
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            f'{self.url}video/',
            {'price': '75.00', 'duration': 90},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session_price = SessionPrice.objects.get(doctor=self.doctor, type='video')
        self.assertEqual(session_price.price, Decimal('75.00'))
        self.assertEqual(session_price.duration, 30)

    def test_negative_price_is_invalid(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.url,
            {'type': 'audio', 'price': '-1.00'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('invalid price', str(response.data))
