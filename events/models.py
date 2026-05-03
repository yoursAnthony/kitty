from django.conf import settings
from django.core.validators import MaxValueValidator, MinLengthValidator, MinValueValidator
from django.db import models


class Event(models.Model):
    """Кото-ивент: событие, на которое можно подать заявку «прийти со своим котом»."""

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_events',
        verbose_name='организатор',
    )
    title = models.CharField(
        'название',
        max_length=120,
        validators=[MinLengthValidator(4)],
    )
    description = models.TextField('описание', blank=True)
    location = models.CharField('место проведения', max_length=200)
    starts_at = models.DateTimeField('начало')
    ends_at = models.DateTimeField('окончание')
    capacity = models.PositiveIntegerField(
        'количество мест',
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    created_at = models.DateTimeField('создан', auto_now_add=True)
    updated_at = models.DateTimeField('обновлён', auto_now=True)

    class Meta:
        verbose_name = 'кото-ивент'
        verbose_name_plural = 'кото-ивенты'
        ordering = ('-starts_at',)
        constraints = [
            models.CheckConstraint(
                check=models.Q(ends_at__gt=models.F('starts_at')),
                name='event_ends_after_starts',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.title} ({self.starts_at:%d.%m.%Y %H:%M})'

    @property
    def approved_applications_count(self) -> int:
        return self.applications.filter(status=Application.Status.APPROVED).count()


class Application(models.Model):
    """Заявка пользователя на участие в ивенте со своим котом."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'на рассмотрении'
        APPROVED = 'approved', 'одобрена'
        REJECTED = 'rejected', 'отклонена'
        CANCELLED = 'cancelled', 'отозвана'

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='ивент',
    )
    cat = models.ForeignKey(
        'cats.Cat',
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='кот',
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='заявитель',
    )
    message_text = models.TextField(
        'текст обращения',
        validators=[MinLengthValidator(1)],
        help_text='Что заявитель пишет организатору при подаче заявки.',
    )
    status = models.CharField(
        'статус',
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField('создана', auto_now_add=True)
    updated_at = models.DateTimeField('обновлена', auto_now=True)

    class Meta:
        verbose_name = 'заявка на ивент'
        verbose_name_plural = 'заявки на ивенты'
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=('event', 'cat'),
                name='unique_application_event_cat',
            ),
        ]

    def __str__(self) -> str:
        return f'Заявка #{self.pk}: {self.cat} → {self.event}'

    @property
    def is_finalized(self) -> bool:
        return self.status in {self.Status.APPROVED, self.Status.REJECTED, self.Status.CANCELLED}


class Dialog(models.Model):
    """Диалог, привязанный к заявке. Создаётся автоматически сигналом."""

    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='dialog',
        verbose_name='заявка',
    )
    is_closed = models.BooleanField('закрыт', default=False)
    created_at = models.DateTimeField('создан', auto_now_add=True)

    class Meta:
        verbose_name = 'диалог'
        verbose_name_plural = 'диалоги'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'Диалог по заявке #{self.application_id}'

    def has_participant(self, user) -> bool:
        if not user or not user.is_authenticated:
            return False
        return user.id in {self.application.applicant_id, self.application.event.organizer_id}


class Message(models.Model):
    """Сообщение в диалоге."""

    dialog = models.ForeignKey(
        Dialog,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='диалог',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='автор',
    )
    text = models.TextField(
        'текст',
        validators=[MinLengthValidator(1)],
    )
    is_read = models.BooleanField('прочитано', default=False)
    created_at = models.DateTimeField('отправлено', auto_now_add=True)

    class Meta:
        verbose_name = 'сообщение'
        verbose_name_plural = 'сообщения'
        ordering = ('created_at',)

    def __str__(self) -> str:
        return f'Сообщение #{self.pk} в диалоге #{self.dialog_id}'
