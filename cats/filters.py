import django_filters
from .models import Cat


class CatFilter(django_filters.FilterSet):
    owner = django_filters.CharFilter(field_name='owner__username', lookup_expr='iexact')
    tag = django_filters.CharFilter(field_name='tags__slug', lookup_expr='iexact')
    birth_year_min = django_filters.NumberFilter(field_name='birth_year', lookup_expr='gte')
    birth_year_max = django_filters.NumberFilter(field_name='birth_year', lookup_expr='lte')

    class Meta:
        model = Cat
        fields = ('owner', 'tag', 'birth_year_min', 'birth_year_max')
