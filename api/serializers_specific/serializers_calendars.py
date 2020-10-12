from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from calendars.models import UserCalendars, UserCalendarLayer


class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCalendars
        fields = '__all__'
        ordering = ('id',)


class CalendarCutSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCalendars
        fields = ('id', 'user', 'calendar_title', 'calendar_description','time_zone',
                  'selected', 'color_id', 'color_background', 'color_foreground','provider','is_active','email')
        ordering = ('id',)

class NewCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCalendars
        fields = ('id', 'user', 'calendar_id', 'calendar_title', 'calendar_description', 'time_zone',
                  'selected', 'color_id', 'color_background', 'color_foreground', 'provider', 'is_active','primary','email','name')
        ordering = ('id',)

class LayersSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCalendarLayer
        fields = '__all__'
        ordering = ('id',)

class NLayersSerializer(serializers.ModelSerializer):
    layer_id = serializers.IntegerField(source='id')
    # user.email =  CurrentUserDefault()  # <= magic!

    class Meta:
        model = UserCalendarLayer
        fields = ('layer_id', 'calendar','ids','layer_title','layer_description', 'time_zone', 'color_id',
        'color_background','color_foreground', 'selected', 'access_role','provider','is_active','primary')
        ordering = ('id',)
