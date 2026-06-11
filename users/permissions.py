from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.conf import settings

class IsVerified(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and getattr(user, 'is_verified', False))
class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and hasattr(request.user, 'doctor')

class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and hasattr(request.user, 'patient')
    
class IsAccountActiveAndUnfrozen(permissions.BasePermission):
    """
    تتحقق مما إذا كان الحساب نشطاً وغير مجمد، 
    وترجع رسائل ثابتة لتطبيق الهاتف مع إيميل الدعم.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True
        
        user = request.user
        support_email = getattr(settings, 'SUPPORT_EMAIL', 'support@afiete.com')
        
        # 1. التحقق من الحظر الكامل
        if not user.is_active:
            raise PermissionDenied({
                "error_code": "ACCOUNT_SUSPENDED",
                "message": "Your account has been temporarily suspended due to a violation of our community guidelines.",
                "admin_email": support_email
            })
            
        # 2. التحقق من تجميد الأموال (بناءً على الحقل الذي سنضيفه)
        if getattr(user, 'is_funds_frozen', False):
            raise PermissionDenied({
                "error_code": "FUNDS_FROZEN",
                "message": "Your financial account and wallet have been frozen due to active reports under investigation.",
                "admin_email": support_email
            })

        return True