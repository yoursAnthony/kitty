from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Чтение разрешено всем, изменение — только владельцу объекта.

    Объект должен иметь атрибут `owner`, ссылающийся на пользователя.
    """

    def has_permission(self, request, view) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, 'owner_id', None) == getattr(request.user, 'id', None)
