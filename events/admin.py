from django.contrib import admin

from .models import CalendarEvent, UserFreeBusy, TemicateEvent, EventTimeSlot, TemicatePollUser


@admin.register(CalendarEvent)
class EventAdmin(admin.ModelAdmin):
    list_display = ('calendar', 'event_id', 'event_title', 'event_description',
                    'html_link', 'status', 'created', 'updated',
                    'location', 'guest_can_modify', 'sequence', 'start',
                    'end', 'attendees', 'reminders', 'recurrence')


@admin.register(UserFreeBusy)
class UserFreeBusyAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserFreeBusy._meta.get_fields()]


@admin.register(TemicateEvent)
class TemicateEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'creator', 'attendees', 'voting', 'free', 'start', 'end')


@admin.register(EventTimeSlot)
class EventTimeSlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'start', 'end', 'event', 'votes')


@admin.register(TemicatePollUser)
class TemicatePollAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_user', 'vote')

