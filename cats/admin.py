from django.contrib import admin

from .models import Achievement, Cat, CatAchievement, CatTag, Tag


@admin.register(Cat)
class CatAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'color', 'birth_year', 'created_at')
    list_filter = ('birth_year', 'tags', 'achievements')
    search_fields = ('name', 'color', 'description')
    autocomplete_fields = ('owner',)
    filter_horizontal = ('tags', 'achievements')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(CatTag)
class CatTagAdmin(admin.ModelAdmin):
    list_display = ('cat', 'tag')


@admin.register(CatAchievement)
class CatAchievementAdmin(admin.ModelAdmin):
    list_display = ('cat', 'achievement', 'achieved_at')
    list_filter = ('achievement',)
