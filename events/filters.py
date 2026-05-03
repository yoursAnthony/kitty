import django_filters

from .models import Application, Event


class EventFilter(django_filters.FilterSet):
    organizer = django_filters.CharFilter(
        field_name='organizer__username', lookup_expr='iexact',
    )
    starts_after = django_filters.IsoDateTimeFilter(
        field_name='starts_at', lookup_expr='gte',
    )
    starts_before = django_filters.IsoDateTimeFilter(
        field_name='starts_at', lookup_expr='lte',
    )

    class Meta:
        model = Event
        fields = ('organizer', 'starts_after', 'starts_before')


class ApplicationFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Application.Status.choices)
    event = django_filters.NumberFilter(field_name='event_id')

    class Meta:
        model = Application
        fields = ('status', 'event')
