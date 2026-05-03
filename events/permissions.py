from rest_framework import permissions


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """Чтение всем; PATCH/DELETE — только организатору ивента."""

    def has_permission(self, request, view) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, 'organizer_id', None) == getattr(request.user, 'id', None)


class IsApplicationParticipant(permissions.BasePermission):
    """Доступ только участнику заявки: организатору ивента или заявителю."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        # obj может быть Application или Dialog/Message — нормализуем до участников
        application = getattr(obj, 'application', None) or getattr(obj, 'dialog', None)
        if application is not None and hasattr(application, 'application'):
            application = application.application
        if application is None:
            application = obj  # значит это сам Application
        applicant_id = getattr(application, 'applicant_id', None)
        organizer_id = getattr(application.event, 'organizer_id', None) if hasattr(application, 'event') else None
        user_id = request.user.id
        return user_id in {applicant_id, organizer_id}


class IsDialogParticipant(permissions.BasePermission):
    """Доступ только участнику диалога (организатор ивента или заявитель заявки)."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        # obj — Dialog или Message
        dialog = obj if hasattr(obj, 'application') else getattr(obj, 'dialog', None)
        if dialog is None:
            return False
        return dialog.has_participant(request.user)
