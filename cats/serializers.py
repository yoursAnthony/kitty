from rest_framework import serializers

from .models import Achievement, Cat, CatAchievement, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ('id', 'name')


class CatAchievementSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='achievement.name', read_only=True)
    achievement_id = serializers.PrimaryKeyRelatedField(
        source='achievement', queryset=Achievement.objects.all(), write_only=True,
    )

    class Meta:
        model = CatAchievement
        fields = ('id', 'name', 'achievement_id', 'achieved_at')
        read_only_fields = ('id', 'achieved_at')


class CatSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field='username', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        source='tags', queryset=Tag.objects.all(),
        many=True, required=False, write_only=True,
    )
    achievements = AchievementSerializer(many=True, read_only=True)
    achievement_ids = serializers.PrimaryKeyRelatedField(
        source='achievements', queryset=Achievement.objects.all(),
        many=True, required=False, write_only=True,
    )
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Cat
        fields = (
            'id', 'owner', 'name', 'color', 'birth_year',
            'description', 'image', 'tags', 'tag_ids',
            'achievements', 'achievement_ids', 'created_at',
        )
        read_only_fields = ('id', 'owner', 'created_at')

    def validate_name(self, value: str) -> str:
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return value
        qs = Cat.objects.filter(owner=request.user, name=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'У вас уже есть кот с такой кличкой.',
            )
        return value


class CatImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cat
        fields = ('id', 'image')
        extra_kwargs = {'image': {'required': True, 'allow_null': False}}
