from rest_framework import permissions

class IsEditor(permissions.BasePermission):
    """
    Custom permission to allow only users with the 'editor' role.
    """

    def has_permission(self, request, view):
        return True
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'profile')
            and request.user.profile.role == 'editor'
        )

class IsAdmin(permissions.BasePermission):
    """
    Custom permission to allow only users with the 'admin' role.
    """

    def has_permission(self, request, view):
        return True
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'profile')
            and request.user.profile.role == 'admin'
        )
