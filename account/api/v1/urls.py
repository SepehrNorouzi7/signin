from django.urls import path
from account.api.v1.views import (
    RegisterLoginView,
    VerifyOTPView,
    CompleteRegistrationView,
    VerifyOTPForLoginView,
    LoginView,
)

urlpatterns = [
    path("register-login/", RegisterLoginView.as_view(), name="register_login"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path(
        "complete-registration/",
        CompleteRegistrationView.as_view(),
        name="complete_registration",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("verify-otp-login/", VerifyOTPForLoginView.as_view(), name="verify_otp_login"),
]
