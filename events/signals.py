from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Application, Dialog, Message


@receiver(post_save, sender=Application)
def create_dialog_for_application(sender, instance: Application, created: bool, **kwargs):
    """При создании заявки автоматически создаём диалог и первое сообщение от заявителя.

    Так пользователь сразу видит начало переписки, а организатор — обращение.
    """
    if not created:
        return
    dialog = Dialog.objects.create(application=instance)
    Message.objects.create(
        dialog=dialog,
        author=instance.applicant,
        text=instance.message_text,
    )
