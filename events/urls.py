from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ApplicationViewSet,
    DialogMessagesViewSet,
    EventViewSet,
    MessageActionViewSet,
)

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='events')
router.register(r'applications', ApplicationViewSet, basename='applications')
router.register(r'messages', MessageActionViewSet, basename='messages')

# Nested: /api/v1/dialogs/{dialog_pk}/messages/  (без drf-nested-routers — вручную)
dialog_messages = DialogMessagesViewSet.as_view({'get': 'list', 'post': 'create'})

urlpatterns = [
    path('', include(router.urls)),
    path('dialogs/<int:dialog_pk>/messages/', dialog_messages, name='dialog-messages'),
]
