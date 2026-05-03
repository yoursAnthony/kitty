from datetime import date

from django.conf import settings
from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models


class Tag(models.Model):
    name = models.CharField(
        'название',
        max_length=64,
        unique=True,
        validators=[MinLengthValidator(2)],
    )
    slug = models.SlugField(
        'slug',
        max_length=64,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[-a-zA-Z0-9_]+$',
                message='Slug может содержать только латиницу, цифры, _ и -.',
            ),
        ],
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


class Achievement(models.Model):
    name = models.CharField('название', max_length=64, unique=True)

    class Meta:
        verbose_name = 'достижение'
        verbose_name_plural = 'достижения'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


def _current_year() -> int:
    return date.today().year


class Cat(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cats',
        verbose_name='владелец',
    )
    name = models.CharField(
        'кличка',
        max_length=32,
        validators=[MinLengthValidator(2)],
    )
    color = models.CharField('окрас', max_length=32)
    birth_year = models.PositiveIntegerField(
        'год рождения',
        blank=True,
        null=True,
        validators=[MinValueValidator(1990), MaxValueValidator(_current_year())],
    )
    description = models.TextField('описание', blank=True)
    image = models.ImageField('фото', upload_to='cats/', blank=True, null=True)
    tags = models.ManyToManyField(
        Tag, through='CatTag', related_name='cats', blank=True,
    )
    achievements = models.ManyToManyField(
        Achievement,
        through='CatAchievement',
        related_name='cats',
        blank=True,
    )
    created_at = models.DateTimeField('создан', auto_now_add=True)

    class Meta:
        verbose_name = 'кот'
        verbose_name_plural = 'коты'
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=('owner', 'name'),
                name='unique_cat_name_per_owner',
            ),
        ]

    def __str__(self) -> str:
        return self.name


class CatAchievement(models.Model):
    cat = models.ForeignKey(
        Cat, on_delete=models.CASCADE, related_name='cat_achievements',
    )
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    achieved_at = models.DateField('дата получения', auto_now_add=True)

    class Meta:
        verbose_name = 'достижение кота'
        verbose_name_plural = 'достижения котов'
        constraints = [
            models.UniqueConstraint(
                fields=('cat', 'achievement'),
                name='unique_cat_achievement',
            ),
        ]


class CatTag(models.Model):
    cat = models.ForeignKey(Cat, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('cat', 'tag'),
                name='unique_cat_tag',
            ),
        ]
