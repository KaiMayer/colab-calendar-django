from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import ForeignKey
from django.utils import timezone
from accounts.models import User
from calendars.models import UserCalendars,UserCalendarLayer

# class Event(models.Model):
#     event_type = models.CharField(max_length=100)
#     activity = models.CharField(max_length=100)
#     address = models.CharField(max_length=200)
#     busy = models.BooleanField(default=False)
#     color_id = models.CharField(max_length=100)
#     created_date = models.DateTimeField(default=timezone.now)
#     start_date = models.DateTimeField(default=timezone.now)
#     end_date = models.DateTimeField(default=timezone.now)
#     occurrence_date = models.DateTimeField(default=timezone.now)
#     invite_others = models.BooleanField(default=False)
#     is_all_day = models.BooleanField(default=False)
#     modify_event = models.BooleanField(default=False)
#     owner = models.ForeignKey(User, on_delete=models.CASCADE)
#     see_list = models.BooleanField(default=False)
#     see_responses = models.BooleanField(default=False)
#     status = models.CharField(max_length=100)
#     title = models.CharField(max_length=100)
#     availability = models.CharField(max_length=100, null=True, blank=True)
#     description = models.CharField(max_length=100, null=True, blank=True)
#     external_identifier = models.CharField(max_length=100, null=True, blank=True)
#     is_detached = models.BooleanField(default=False)
#     is_recurring = models.BooleanField(default=False)
#     organizer = models.CharField(max_length=200, null=True, blank=True)
#
#     class Meta:
#         verbose_name = 'event'
#         verbose_name_plural = 'events'
#
#     def __str__(self):
#         return '% %'.format(str(self.id), self.title)


class CalendarEvent(models.Model):
    calendar = models.ForeignKey(UserCalendars, on_delete=models.CASCADE)
    event_id = models.CharField("Event ID", max_length=255, unique=True, null=True)
    event_title = models.TextField("Event title", max_length=1000, blank=True, null=True)
    event_description = models.TextField("Event description", max_length=8100, blank=True, null=True)
    html_link = models.CharField("HTML link", max_length=255, blank=True, null=True)
    color_id = models.CharField("Color ID", max_length=20, blank=True, null=True)
    status = models.CharField("Status", max_length=10, blank=True, null=True)
    transparency = models.CharField("Transparency",  max_length=30, default="opaque", blank=True, null=True)
    visibility = models.CharField("Visibility", max_length=30, default = "default", blank=True, null=True)
    created = models.DateTimeField("Datetime created", blank=True, null=True)
    updated = models.DateTimeField("Datetime updated", blank=True, null=True)
    location = models.CharField("Location", max_length=1024, blank=True, null=True)
    guest_can_modify = models.BooleanField("Guest can modify", default=False, blank=True)
    guest_can_invite = models.BooleanField("Guest can invite", default=True, blank=True)
    guest_can_see_others = models.BooleanField("Guest can invite", default=True, blank=True)
    sequence = models.IntegerField(blank=True, null=True)
    creator = JSONField(blank=True, null=True)
    organizer = JSONField(blank=True, null=True)
    start = JSONField(blank=True, null=True)
    end = JSONField(blank=True, null=True)
    attendees = JSONField(blank=True, null=True)
    reminders = JSONField(blank=True, null=True)
    recurrence = JSONField(blank=True, null=True)

    class Meta:
        verbose_name = 'calendar event'
        verbose_name_plural = 'calendar events'
        ordering = ('id',)

    def __str__(self):
        return self.event_id


class TemicatePollUser(models.Model):
    event_user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote = models.CharField(max_length=10, default="not_voted",
                            choices=(("not_voted", "not_voted"), ("going", "going"),
                                     ("not_going", "not_going"), ("maybe", "maybe"),))
    color = models.CharField(max_length=25, null=True, blank=True)
    busy = models.BooleanField(default=False)
    notifications = models.BooleanField(default=False)

    class Meta:
        ordering = ('id',)
        verbose_name = "user poll"
        verbose_name_plural = "user polls"


class TemicateEvent(models.Model):
    layer = models.ForeignKey(UserCalendarLayer, null = True, on_delete=models.CASCADE)
    event_title = models.TextField(max_length=1000, default="No title")
    event_activity = models.TextField(max_length=200, null=True, blank=True)
    event_description = models.TextField(max_length=8100, blank=True, null=True)
    location = models.CharField("Location", max_length=1024, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, blank=True, related_name="event")
    polls = models.ManyToManyField(TemicatePollUser, blank=True, related_name="event")
    attendees = JSONField(blank=True, null=True, default=list)
    voting = JSONField(blank=True, null=True)
    free = JSONField(blank=True, null=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    event_start = models.DateTimeField(blank=True, null=True)
    event_end = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=25, default="pending",
                              choices=(("pending", "pending"), ("confirmed", "confirmed")))
    users_can_modify = models.BooleanField(blank=True)
    users_can_invite = models.BooleanField(blank=True)

    class Meta:
        verbose_name = 'temicate event'
        verbose_name_plural = 'temicate events'
        ordering = ('id',)



class EventTimeSlot(models.Model):
    event = models.ForeignKey(TemicateEvent, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()
    votes = models.IntegerField(default=0)
    voted_users = models.ManyToManyField(User, related_name="timeslot", blank=True)

    class Meta:
        ordering = ('id',)


class UserFreeBusy(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    busy = JSONField(blank=True, null=True)
    last_sync = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'user free busy'
        verbose_name_plural = 'user free busy'
        ordering = ('id',)
