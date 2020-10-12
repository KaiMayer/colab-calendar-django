from django.db import models
from accounts.models import User
from django.contrib.postgres.fields import JSONField
from django.utils import timezone


class UserCalendars(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    calendar_id = models.CharField("Calendar ID", max_length=255, unique=True, null=True)
    # calendar_id = models.CharField("Calendar ID", max_length=255, null=True)
    calendar_title = models.CharField("Calendar title", max_length=250, blank=True, null=True)
    calendar_description = models.CharField("Calendar description", max_length=200, blank=True, null=True)
    primary = models.BooleanField("Primary", default=False, blank=True)
    time_zone = models.CharField("Time zone", max_length=128, blank=True, null=True)
    color_id = models.CharField("Color ID", max_length=10, blank=True, null=True)
    color_background = models.CharField("Background color", max_length=10, blank=True, null=True)
    color_foreground = models.CharField("Foreground color", max_length=10, blank=True, null=True)
    selected = models.BooleanField("Selected", default=True, blank=True)
    access_role = models.CharField("Access role", max_length=50, default="owner", blank=True, null=True)
    default_reminders = JSONField("Default remainders", blank=True, null=True)
    notifications = JSONField("Notification settings", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    provider = models.CharField("Provider", max_length=30, default="teamicate", blank=True, null=True)
    is_active = models.BooleanField("Is active", default=True, blank=True)
    name = models.CharField("Calendar name", max_length=250, blank=True, null=True)
    email = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = 'user calendar'
        verbose_name_plural = 'user calendars'
        ordering = ('id',)

    def __str__(self):
        return self.calendar_title


class UserCalendarLayer(models.Model):
    ids = models.CharField(max_length=255, null=True)
    calendar = models.ForeignKey(UserCalendars, on_delete=models.CASCADE)
    layer_title = models.CharField("Layer title", max_length=250, blank=True, null=True)
    layer_description = models.CharField("Layer description", max_length=200, blank=True, null=True)
    primary = models.BooleanField("Primary", default=False, blank=True)
    time_zone = models.CharField("Time zone", max_length=128, blank=True, null=True)
    color_id = models.CharField("Color ID", max_length=10, blank=True, null=True)
    color_background = models.CharField("Background color", max_length=10, blank=True, null=True)
    color_foreground = models.CharField("Foreground color", max_length=10, blank=True, null=True)
    selected = models.BooleanField("Selected", default=True, blank=True)
    access_role = models.CharField("Access role", max_length=50, default="owner", blank=True, null=True)
    default_reminders = JSONField("Default remainders", blank=True, null=True)
    notifications = JSONField("Notification settings", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    provider = models.CharField("Provider", max_length=30, default="temaicate", blank=True, null=True)
    is_active = models.BooleanField("Is active", default=True, blank=True)

    class Meta:
        verbose_name = 'user calendar layer'
        verbose_name_plural = 'user calendar layers'
