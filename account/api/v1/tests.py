from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.cache import cache
from account.models import CustomUser, OTP


class AuthTests(APITestCase):

    def setUp(self):
        self.mobile_number = "09123456789"
        self.invalid_mobile_number = "123456"
        self.valid_otp = "123456"
        self.invalid_otp = "000000"

        cache.clear()

        self.user = CustomUser.objects.create(mobile_number=self.mobile_number)

    def test_register_user(self):
        url = reverse("register_login")
        data = {"mobile_number": "09123456788"}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("OTP sent to your mobile number.", response.data["detail"])

    def test_register_user_with_invalid_number(self):
        url = reverse("register_login")
        data = {"mobile_number": self.invalid_mobile_number}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid mobile number", response.data["detail"])

    def test_verify_otp_success(self):
        url = reverse("verify_otp")

        cache.set(f"otp_{self.mobile_number}", self.valid_otp)

        data = {"mobile_number": self.mobile_number, "code": self.valid_otp}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("OTP verified", response.data["detail"])

    def test_verify_otp_invalid(self):
        url = reverse("verify_otp")

        cache.set(f"otp_{self.mobile_number}", self.valid_otp)

        data = {"mobile_number": self.mobile_number, "code": self.invalid_otp}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid OTP code", response.data["detail"])

    def test_login_user(self):
        url = reverse("login_mobile")
        data = {"mobile_number": self.mobile_number}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("OTP sent to your mobile number.", response.data["detail"])

    def test_verify_otp_for_login_success(self):
        url = reverse("verify_otp_login")

        cache.set(f"otp_{self.mobile_number}", self.valid_otp)

        data = {"mobile_number": self.mobile_number, "code": self.valid_otp}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Login successful.", response.data["detail"])

    def test_failed_attempts_block_ip(self):
        url = reverse("verify_otp_login")

        for _ in range(3):
            response = self.client.post(
                url, {"mobile_number": self.mobile_number, "code": self.invalid_otp}
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            url, {"mobile_number": self.mobile_number, "code": self.invalid_otp}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Your IP is blocked", response.data["detail"])
