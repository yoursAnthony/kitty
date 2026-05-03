from django.contrib import admin

from .models import Application, Dialog, Event, Message


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'organizer', 'starts_at', 'ends_at', 'capacity')
    list_filter = ('starts_at',)
    search_fields = ('title', 'location', 'description')
    autocomplete_fields = ('organizer',)
    date_hierarchy = 'starts_at'


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'cat', 'applicant', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('event__title', 'cat__name', 'applicant__username')
    autocomplete_fields = ('event', 'cat', 'applicant')


@admin.register(Dialog)
class DialogAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'is_closed', 'created_at')
    list_filter = ('is_closed',)
    search_fields = ('id', 'application__id', 'application__event__title')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'dialog', 'author', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('text', 'author__username')
    autocomplete_fields = ('dialog', 'author')
