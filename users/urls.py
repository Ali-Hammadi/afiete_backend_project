from django.urls import path
from .views import *
from .views import LoginView , LogoutView
urlpatterns = [
   path('login/', LoginView.as_view(), name='login'),
   path('otp/resend', ResendOtpView.as_view(), name='resend-otp'),
   path('otp/verify', VerifyOtpView.as_view(), name='verify-otp'),
   path('logout/', LogoutView.as_view(), name='logout'),
   path('email/reset',EmailResetView.as_view(),name='email-reset'),
   path('password/change',PasswordResetView.as_view(),name='password-reset'),

   # activate and deactivate account
   path('deactivate', DeactivateAccountView.as_view(), name='deactivate-account'),
   path('activate', ActivateUserView.as_view(), name= 'activate-user'),
   
   # forget password
   path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
   path('auth/verify-otp/', ForgetPasswordVerifyOtpView.as_view(), name='verify-otp'),
   path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password')
]

# urlpatterns = [

#     path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
# ]