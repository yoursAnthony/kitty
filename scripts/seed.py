"""Заполняет БД демо-данными для скриншотов отчёта.

Запуск из корня проекта:
    python manage.py shell < scripts/seed.py
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from cats.models import Achievement, Cat, Tag
from events.models import Application, Event, Message

User = get_user_model()


def get_or_create_user(username: str, password: str, **extra):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': f'{username}@example.com', **extra},
    )
    if created or not user.check_password(password):
        user.set_password(password)
    for k, v in extra.items():
        setattr(user, k, v)
    user.save()
    return user


alice = get_or_create_user('alice', 'P@ssw0rd!2026Long')
bob = get_or_create_user('bob', 'P@ssw0rd!2026Long')
admin = get_or_create_user(
    'admin', 'AdminP@ss!2026Long',
    is_staff=True, is_superuser=True,
)

tag_fluffy, _ = Tag.objects.get_or_create(name='Пушистый', slug='fluffy')
tag_calm, _ = Tag.objects.get_or_create(name='Спокойный', slug='calm')
tag_playful, _ = Tag.objects.get_or_create(name='Игривый', slug='playful')

ach_long_hair, _ = Achievement.objects.get_or_create(name='Длинная шерсть')
ach_champion, _ = Achievement.objects.get_or_create(name='Чемпион двора')
ach_purr, _ = Achievement.objects.get_or_create(name='Громко мурлычет')


def make_cat(owner, name, color, year, description, tags=(), achievements=()):
    cat, _ = Cat.objects.get_or_create(
        owner=owner, name=name,
        defaults={'color': color, 'birth_year': year, 'description': description},
    )
    if tags:
        cat.tags.set(tags)
    if achievements:
        cat.achievements.set(achievements)
    return cat


make_cat(alice, 'Пушок', 'Белый', 2019, 'Любит спать на батарее', (tag_fluffy, tag_calm), (ach_long_hair,))
make_cat(alice, 'Барсик', 'Серый полосатый', 2021, 'Очень игривый, грызёт провода', (tag_playful,), (ach_purr,))
make_cat(bob, 'Мурзик', 'Чёрный', 2018, 'Старый и мудрый кот', (tag_calm,), (ach_champion, ach_purr))


# ─── События и заявки ─────────────────────────────────────────────
def make_event(organizer, title, description, location, days_ahead, capacity):
    starts_at = timezone.now() + timedelta(days=days_ahead, hours=12)
    ends_at = starts_at + timedelta(hours=3)
    event, _ = Event.objects.get_or_create(
        organizer=organizer, title=title,
        defaults={
            'description': description, 'location': location,
            'starts_at': starts_at, 'ends_at': ends_at, 'capacity': capacity,
        },
    )
    return event


event_photoshoot = make_event(
    alice,
    'Фотосессия в парке Горького',
    'Будем фотографировать котов в осенней листве. Профессиональный фотограф.',
    'Москва, Парк Горького, у Главного входа',
    days_ahead=14, capacity=5,
)
event_meetup = make_event(
    bob,
    'Встреча владельцев британских котов',
    'Знакомимся, обмениваемся опытом ухода. Чай и угощения для котов.',
    'Москва, кото-кафе «Пушистый рай»',
    days_ahead=7, capacity=8,
)


def make_application(event, cat, applicant, message_text, status=Application.Status.PENDING):
    app, created = Application.objects.get_or_create(
        event=event, cat=cat,
        defaults={'applicant': applicant, 'message_text': message_text, 'status': status},
    )
    if not created:
        app.status = status
        app.save(update_fields=('status', 'updated_at'))
    return app


# bob → photoshoot, заявка одобрена + переписка в диалоге
app1 = make_application(
    event_photoshoot, Cat.objects.get(owner=bob, name='Мурзик'), bob,
    'Привет! Хочу прийти со своим Мурзиком, ему 8 лет, очень фотогеничный.',
    status=Application.Status.APPROVED,
)
# alice → meetup, заявка на рассмотрении
app2 = make_application(
    event_meetup, Cat.objects.get(owner=alice, name='Барсик'), alice,
    'Барсик любит знакомиться. Можно прийти?',
)

# Расширим переписку в диалоге одобренной заявки (если только что создана сигналом)
dialog1 = app1.dialog
if dialog1.messages.count() < 3:
    Message.objects.get_or_create(
        dialog=dialog1, author=alice,
        text='Здорово, ждём вас! Возьмите с собой воду для Мурзика.',
    )
    Message.objects.get_or_create(
        dialog=dialog1, author=bob,
        text='Спасибо! Будем в 15:50, чтобы успеть к старту.',
    )
# Закрыть диалог одобренной заявки
if not dialog1.is_closed and app1.status == Application.Status.APPROVED:
    dialog1.is_closed = True
    dialog1.save(update_fields=('is_closed',))


print(
    'Seed OK:',
    User.objects.count(), 'users,',
    Cat.objects.count(), 'cats,',
    Event.objects.count(), 'events,',
    Application.objects.count(), 'applications,',
    Message.objects.count(), 'messages',
)
