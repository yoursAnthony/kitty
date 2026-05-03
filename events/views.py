from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import ApplicationFilter, EventFilter
from .models import Application, Dialog, Event, Message
from .permissions import (
    IsApplicationParticipant,
    IsDialogParticipant,
    IsOrganizerOrReadOnly,
)
from .serializers import (
    ApplicationSerializer,
    ApplicationStatusSerializer,
    DialogSerializer,
    EventSerializer,
    MessageCreateSerializer,
    MessageSerializer,
)


class EventViewSet(viewsets.ModelViewSet):
    """CRUD кото-ивентов + nested список заявок."""

    queryset = Event.objects.select_related('organizer').all()
    serializer_class = EventSerializer
    permission_classes = (IsOrganizerOrReadOnly,)
    filterset_class = EventFilter
    search_fields = ('title', 'location')
    ordering_fields = ('starts_at', 'created_at', 'capacity')
    ordering = ('-starts_at',)

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=True, methods=('get',), url_path='applications')
    def applications(self, request, pk=None):
        """Заявки на ивент: организатор видит все, остальные — только свои."""
        event = self.get_object()
        qs = event.applications.select_related('cat', 'applicant')
        if event.organizer_id != request.user.id:
            qs = qs.filter(applicant=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ApplicationSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = ApplicationSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class ApplicationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Заявки на ивенты: создать, посмотреть свои, сменить статус."""

    serializer_class = ApplicationSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = ApplicationFilter
    ordering_fields = ('created_at', 'status')
    ordering = ('-created_at',)

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Application.objects.none()
        # Видим заявки, где мы заявитель ИЛИ организатор ивента
        return (
            Application.objects
            .select_related('cat', 'applicant', 'event', 'event__organizer', 'dialog')
            .filter(Q(applicant=user) | Q(event__organizer=user))
            .distinct()
        )

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)

    @action(
        detail=True,
        methods=('post',),
        url_path='set_status',
        permission_classes=(IsAuthenticated, IsApplicationParticipant),
    )
    def set_status(self, request, pk=None):
        """Сменить статус заявки. Бизнес-правила в ApplicationStatusSerializer."""
        application = self.get_object()
        serializer = ApplicationStatusSerializer(
            data=request.data,
            context={'request': request, 'application': application},
        )
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']
        application.status = new_status
        application.save(update_fields=('status', 'updated_at'))

        # Если заявка ушла в финальное состояние — закрываем диалог
        if application.is_finalized:
            dialog = getattr(application, 'dialog', None)
            if dialog is not None and not dialog.is_closed:
                dialog.is_closed = True
                dialog.save(update_fields=('is_closed',))

        return Response(
            ApplicationSerializer(application, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


class DialogMessagesViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """GET /dialogs/{dialog_pk}/messages/ — список; POST — отправить сообщение."""

    permission_classes = (IsAuthenticated,)
    ordering = ('created_at',)

    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def _get_dialog(self) -> Dialog:
        try:
            dialog = (
                Dialog.objects
                .select_related('application', 'application__event')
                .get(pk=self.kwargs['dialog_pk'])
            )
        except Dialog.DoesNotExist:
            raise NotFound('Диалог не найден.')
        if not dialog.has_participant(self.request.user):
            raise NotFound('Диалог не найден.')
        return dialog

    def get_queryset(self):
        dialog = self._get_dialog()
        return dialog.messages.select_related('author').all()

    def create(self, request, *args, **kwargs):
        dialog = self._get_dialog()
        if dialog.is_closed:
            raise PermissionDenied('Диалог закрыт — писать в него нельзя.')
        write_serializer = MessageCreateSerializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        message = Message.objects.create(
            dialog=dialog,
            author=request.user,
            text=write_serializer.validated_data['text'],
        )
        read_serializer = MessageSerializer(message, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class MessageActionViewSet(viewsets.GenericViewSet):
    """Эндпоинт /messages/{pk}/mark_read/."""

    queryset = Message.objects.select_related('dialog', 'dialog__application', 'dialog__application__event').all()
    serializer_class = MessageSerializer
    permission_classes = (IsAuthenticated, IsDialogParticipant)

    def get_object(self):
        obj = super().get_object()
        # IsDialogParticipant ожидает Message с .dialog
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=True, methods=('post',), url_path='mark_read')
    def mark_read(self, request, pk=None):
        message: Message = self.get_object()
        # Только не-автор может отметить как прочитанное
        if message.author_id == request.user.id:
            return Response(
                {'detail': 'Свои сообщения нельзя отмечать прочитанными.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not message.is_read:
            message.is_read = True
            message.save(update_fields=('is_read',))
        return Response(
            MessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )
