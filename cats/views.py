from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import (
    IsAdminUser,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from core.permissions import IsOwnerOrReadOnly

from .filters import CatFilter
from .models import Achievement, Cat, Tag
from .serializers import (
    AchievementSerializer,
    CatImageSerializer,
    CatSerializer,
    TagSerializer,
)


class CatViewSet(viewsets.ModelViewSet):
    """CRUD котов + загрузка фото.

    - GET — публично, с фильтрами/поиском/пагинацией.
    - POST/PATCH/DELETE — только для владельца кота.
    """
    queryset = Cat.objects.select_related('owner').prefetch_related(
        'tags', 'achievements',
    )
    serializer_class = CatSerializer
    permission_classes = (IsOwnerOrReadOnly,)
    filterset_class = CatFilter
    search_fields = ('name', 'color', 'description')
    ordering_fields = ('created_at', 'birth_year', 'name')
    ordering = ('-created_at',)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(
        detail=True,
        methods=('post',),
        url_path='upload_image',
        parser_classes=(MultiPartParser, FormParser, JSONParser),
        serializer_class=CatImageSerializer,
    )
    def upload_image(self, request, pk=None):
        cat = self.get_object()
        serializer = self.get_serializer(cat, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class AchievementViewSet(viewsets.ModelViewSet):
    """Справочник достижений.

    - GET — публично.
    - POST/PATCH/DELETE — только staff.
    """
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    search_fields = ('name',)
    ordering_fields = ('name',)

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return (IsAuthenticatedOrReadOnly(),)
        return (IsAdminUser(),)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Справочник тегов (только чтение)."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    search_fields = ('name', 'slug')
