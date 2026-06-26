from rest_framework import permissions


class IsPrescribingDoctor(permissions.BasePermission):
    message = 'Only doctors can access prescription doctor endpoints.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if hasattr(user, 'therapist'):
            return False

        return hasattr(user, 'doctor')
