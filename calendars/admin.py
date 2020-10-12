from django.contrib import admin
from .models import UserCalendars, UserCalendarLayer


@admin.register(UserCalendars)
class UserCalendarLayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'calendar_id', 'calendar_title', 'calendar_description',
                    'primary', 'time_zone', 'color_id', 'color_background',
                    'color_foreground', 'selected', 'access_role', 'created_at')


@admin.register(UserCalendarLayer)
class UserCalendarsAdmin(admin.ModelAdmin):
    list_display = ('ids', 'calendar', 'created_at')
