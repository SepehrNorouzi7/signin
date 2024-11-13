from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from account.models import CustomUser, OTP
from account.api.v1.serializers import (
    RegisterSerializer,
    OTPSerializer,
    UserDetailSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
)
import random
from account.api.utils import get_client_ip


def send_sms(mobile_number, code):
    print(f"Sending SMS to {mobile_number}: Your OTP code is {code}")


def generate_otp():
    code = [str(random.randint(0, 9)) for _ in range(6)]
    return "".join(code)


class RegisterLoginView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mobile_number = serializer.validated_data["mobile_number"]

        if len(mobile_number) != 11 or not mobile_number.isnumeric():
            return Response(
                {"detail": "Invalid mobile number. It must be exactly 11 digits."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ip = get_client_ip(request)
        blocked = cache.get(f"block_{ip}")
        if blocked:
            return Response(
                {"detail": "Your IP is blocked. Try again later."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user = CustomUser.objects.get(mobile_number=mobile_number)
            return Response(
                {"detail": "User exists. Please log in with your password."},
                status=status.HTTP_200_OK,
            )
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create(mobile_number=mobile_number)
            code = generate_otp()
            OTP.objects.create(user=user, code=code)
            send_sms(mobile_number, code)
            cache.set(f"otp_{mobile_number}", code, timeout=60)
            return Response(
                {"detail": "OTP sent to your mobile number."},
                status=status.HTTP_201_CREATED,
            )


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = OTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data.get("code")

        if len(code) != 6 or not code.isnumeric():
            return Response(
                {"detail": "Invalid OTP code. It must be exactly 6 digits."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ip = get_client_ip(request)
        if cache.get(f"block_{ip}"):
            return Response(
                {"detail": "Your IP is blocked. Try again later."},
                status=status.HTTP_403_FORBIDDEN,
            )

        mobile_number = serializer.validated_data.get("mobile_number")
        cached_code = cache.get(f"otp_{mobile_number}")
        if cached_code and cached_code == code:
            user, created = CustomUser.objects.get_or_create(
                mobile_number=mobile_number
            )
            if not created:
                return Response(
                    {"detail": "OTP verified. User already registered."},
                    status=status.HTTP_200_OK,
                )

            cache.delete(f"otp_{mobile_number}")
            return Response(
                {
                    "detail": "OTP verified. Please provide your personal information.",
                    "user_id": user.id,
                },
                status=status.HTTP_200_OK,
            )
        else:
            fail_count = cache.get(f"fail_{ip}") or 0
            fail_count += 1
            cache.set(f"fail_{ip}", fail_count, timeout=3600)
            if fail_count >= 3:
                cache.set(f"block_{ip}", True, timeout=3600)
                return Response(
                    {
                        "detail": "Too many failed attempts. Your IP is blocked for 1 hour."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            return Response(
                {"detail": "Invalid OTP code."}, status=status.HTTP_400_BAD_REQUEST
            )


class CompleteRegistrationView(generics.UpdateAPIView):
    serializer_class = UserDetailSerializer
    queryset = CustomUser.objects.all()

    def put(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Registration complete."}, status=status.HTTP_200_OK)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mobile_number = serializer.validated_data["mobile_number"]

        if len(mobile_number) != 11 or not mobile_number.isnumeric():
            return Response(
                {"detail": "Invalid mobile number. It must be exactly 11 digits."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ip = get_client_ip(request)
        block_key = f"block_{ip}"

        if cache.get(block_key):
            return Response(
                {"detail": "Your IP is blocked. Try again later."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user = CustomUser.objects.get(mobile_number=mobile_number)
            code = generate_otp()
            OTP.objects.create(user=user, code=code)
            send_sms(mobile_number, code)
            cache.set(f"otp_{mobile_number}", code, timeout=60)
            return Response(
                {"detail": "OTP sent to your mobile number."}, status=status.HTTP_200_OK
            )
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "Mobile number not registered."},
                status=status.HTTP_404_NOT_FOUND,
            )


class VerifyOTPForLoginView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mobile_number = serializer.validated_data["mobile_number"]
        code = serializer.validated_data["code"]

        if len(code) != 6 or not code.isnumeric():
            return Response(
                {"detail": "Invalid OTP code. It must be exactly 6 digits."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ip = get_client_ip(request)
        block_key = f"block_{ip}"

        if cache.get(block_key):
            return Response(
                {"detail": "Your IP is blocked. Try again later."},
                status=status.HTTP_403_FORBIDDEN,
            )

        cached_code = cache.get(f"otp_{mobile_number}")
        if cached_code and cached_code == code:
            cache.delete(f"otp_{mobile_number}")
            return Response({"detail": "Login successful."}, status=status.HTTP_200_OK)
        else:
            fail_key = f"fail_login_{ip}"
            fail_count = cache.get(fail_key) or 0
            fail_count += 1
            cache.set(fail_key, fail_count, timeout=3600)

            if fail_count >= 3:
                cache.set(block_key, True, timeout=3600)
                return Response(
                    {
                        "detail": "Too many failed attempts. Your IP is blocked for 1 hour."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            return Response(
                {"detail": "Invalid OTP code."}, status=status.HTTP_400_BAD_REQUEST
            )
