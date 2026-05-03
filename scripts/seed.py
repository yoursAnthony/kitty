"""Заполняет БД демо-данными для скриншотов отчёта.

Запуск из корня проекта:
    python manage.py shell < scripts/seed.py
"""
from django.contrib.auth import get_user_model

from cats.models import Achievement, Cat, Tag

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

print('Seed OK:', User.objects.count(), 'users,', Cat.objects.count(), 'cats')
