from django.utils import timezone
from rest_framework import serializers

from cats.models import Cat

from .models import Application, Dialog, Event, Message


class EventSerializer(serializers.ModelSerializer):
    organizer = serializers.SlugRelatedField(slug_field='username', read_only=True)
    approved_count = serializers.IntegerField(source='approved_applications_count', read_only=True)

    class Meta:
        model = Event
        fields = (
            'id', 'organizer', 'title', 'description', 'location',
            'starts_at', 'ends_at', 'capacity',
            'approved_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'organizer', 'created_at', 'updated_at')

    def validate(self, attrs):
        starts_at = attrs.get('starts_at') or getattr(self.instance, 'starts_at', None)
        ends_at = attrs.get('ends_at') or getattr(self.instance, 'ends_at', None)
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError(
                {'ends_at': 'Окончание ивента должно быть позже начала.'},
            )
        # На create: starts_at должен быть в будущем
        if self.instance is None and starts_at and starts_at <= timezone.now():
            raise serializers.ValidationError(
                {'starts_at': 'Нельзя создавать ивент в прошлом.'},
            )
        return attrs


class MessageSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'dialog', 'author', 'text', 'is_read', 'created_at')
        read_only_fields = ('id', 'dialog', 'author', 'is_read', 'created_at')


class DialogSerializer(serializers.ModelSerializer):
    application_id = serializers.IntegerField(source='application.id', read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Dialog
        fields = ('id', 'application_id', 'is_closed', 'created_at', 'last_message')
        read_only_fields = fields

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if not msg:
            return None
        return MessageSerializer(msg, context=self.context).data


class ApplicationSerializer(serializers.ModelSerializer):
    applicant = serializers.SlugRelatedField(slug_field='username', read_only=True)
    cat_name = serializers.CharField(source='cat.name', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    dialog_id = serializers.IntegerField(source='dialog.id', read_only=True)

    class Meta:
        model = Application
        fields = (
            'id', 'event', 'event_title', 'cat', 'cat_name',
            'applicant', 'message_text', 'status',
            'dialog_id', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'event_title', 'cat_name', 'applicant',
            'status', 'dialog_id', 'created_at', 'updated_at',
        )

    def validate(self, attrs):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return attrs

        event: Event = attrs.get('event')
        cat: Cat = attrs.get('cat')

        if event is None or cat is None:
            return attrs

        # 1. Нельзя подавать заявку на собственный ивент
        if event.organizer_id == request.user.id:
            raise serializers.ValidationError(
                {'event': 'Вы организатор этого ивента — заявку подавать не нужно.'},
            )

        # 2. Кот должен принадлежать заявителю
        if cat.owner_id != request.user.id:
            raise serializers.ValidationError(
                {'cat': 'Можно подать заявку только со своим котом.'},
            )

        # 3. Ивент должен ещё не начаться
        if event.starts_at <= timezone.now():
            raise serializers.ValidationError(
                {'event': 'Ивент уже начался — заявку подавать поздно.'},
            )

        # 4. Не дублировать существующую заявку (event, cat)
        if Application.objects.filter(event=event, cat=cat).exists():
            raise serializers.ValidationError(
                {'cat': 'Заявка с этим котом на этот ивент уже подана.'},
            )

        return attrs


class ApplicationStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Application.Status.choices)

    def validate_status(self, value):
        application: Application = self.context['application']
        request = self.context['request']
        user_id = request.user.id

        # Финальные статусы — заявку уже нельзя двигать
        if application.is_finalized:
            raise serializers.ValidationError(
                'Заявка уже в финальном состоянии — статус сменить нельзя.',
            )

        # Cancelled — только заявитель может отозвать свою заявку
        if value == Application.Status.CANCELLED:
            if user_id != application.applicant_id:
                raise serializers.ValidationError(
                    'Отозвать заявку может только её автор.',
                )
            return value

        # Approved/Rejected — только организатор ивента
        if value in (Application.Status.APPROVED, Application.Status.REJECTED):
            if user_id != application.event.organizer_id:
                raise serializers.ValidationError(
                    'Менять статус заявки может только организатор ивента.',
                )
            # Capacity-проверка при approved
            if value == Application.Status.APPROVED:
                approved_count = application.event.approved_applications_count
                if approved_count >= application.event.capacity:
                    raise serializers.ValidationError(
                        'На ивенте больше нет свободных мест.',
                    )
            return value

        # Pending — невалидный обратный переход
        raise serializers.ValidationError(
            'Недопустимый целевой статус.',
        )


class MessageCreateSerializer(serializers.ModelSerializer):
    """Используется для POST /dialogs/{id}/messages/."""

    class Meta:
        model = Message
        fields = ('text',)
