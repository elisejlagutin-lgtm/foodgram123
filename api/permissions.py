from rest_framework import permissions


class IsAuthorOrIsAdminOrReadOnly(permissions.BasePermission):
    """Пермишен для разрешению на работу автору, админу или анонимному читателю"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_anonymous:
            return False

        if request.user.is_superuser:
            return True

        if hasattr(obj, 'author') and request.user == obj.author:
            return True

        return False
