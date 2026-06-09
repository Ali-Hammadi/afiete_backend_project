from rest_framework import permissions

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