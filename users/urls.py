from django.urls import path
from .views import (
    LoginView, LogoutView, ResendOtpView, VerifyOtpView,
    EmailResetView, PasswordResetView, DeactivateAccountView, 
    ActivateUserView, ForgotPasswordView, ForgetPasswordVerifyOtpView, ResetPasswordView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('activate/', ActivateUserView.as_view(), name='activate-user'),
    path('deactivate/', DeactivateAccountView.as_view(), name='deactivate-account'),
    path('otp/resend/', ResendOtpView.as_view(), name='resend-otp'),
    path('otp/verify/', VerifyOtpView.as_view(), name='verify-otp'),
    path('email/reset/', EmailResetView.as_view(), name='email-reset'),
    path('password/change/', PasswordResetView.as_view(), name='password-change'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('forgot-password/verify-otp/', ForgetPasswordVerifyOtpView.as_view(), name='forgot-password-verify-otp'),
    path('forgot-password/reset/', ResetPasswordView.as_view(), name='reset-password'),
]