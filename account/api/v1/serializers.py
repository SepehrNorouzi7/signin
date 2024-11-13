from rest_framework import serializers
from account.models import CustomUser, OTP


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("mobile_number",)


class OTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6, required=False)


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email")


class LoginSerializer(serializers.Serializer):
    mobile_number = serializers.CharField()


class VerifyOTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField()
    code = serializers.CharField()
