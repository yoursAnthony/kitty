from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AchievementViewSet, CatViewSet, TagViewSet

router = DefaultRouter()
router.register(r'cats', CatViewSet, basename='cats')
router.register(r'achievements', AchievementViewSet, basename='achievements')
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
]
