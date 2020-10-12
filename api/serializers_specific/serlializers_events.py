import datetime

from rest_framework import serializers

from accounts.models import User
from events.models import CalendarEvent, TemicateEvent, TemicatePollUser, EventTimeSlot

class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = '__all__'
        ordering = ('id',)


class EventAttendeesSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    optional = serializers.BooleanField(default=False)
    comment = serializers.CharField(max_length=1024, required=False)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class EventReminderOverrideSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=[("email", "email"), ("popup", "popup")],
                                     error_messages={'invalid_choice': "'{input}' is not a valid choice."
                                                                       "Use instead: 'email' or 'popup'"})
    minutes = serializers.IntegerField(min_value=0, max_value=40320)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class EventReminderSerializer(serializers.Serializer):
    overrides = EventReminderOverrideSerializer(required=True, many=True)
    useDefault = serializers.BooleanField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    def validate(self, data):
        if data["useDefault"]:
            raise serializers.ValidationError("Cannot specify both default reminders and overrides at the same time."
                                              "You should use 'useDefault': false")
        return data


class EventCreateSerializer(serializers.Serializer):
    calendarId = serializers.CharField(default="primary")
    summary = serializers.CharField(required=False, max_length=1000)
    description = serializers.CharField(required=False, max_length=8100)
    location = serializers.CharField(required=False, max_length=1024)
    colorId = serializers.ChoiceField(required=False, choices=[(id, id) for id in range(12)])
    attendees = EventAttendeesSerializer(required=False, many=True)
    status = serializers.ChoiceField(
        required=False, default="confirmed",
        choices=[("confirmed", "confirmed"), ("tentative", "tentative"), ("cancelled", "cancelled")])
    transparency = serializers.ChoiceField(
        required=False, default="opaque",
        choices=[("opaque", "opaque"), ("transparent", "transparent")])
    visibility = serializers.ChoiceField(
        required=False, default="default",
        choices=[("default", "default"), ("public", "public"), ("private", "private"), ("confidential", "confidential")])
    guestsCanInviteOthers = serializers.BooleanField(default=True)
    guestsCanModify = serializers.BooleanField(default=False)
    guestsCanSeeOtherGuests = serializers.BooleanField(default=True)
    reminders = EventReminderSerializer(required=False)

    def create(self, validated_data):
        return EventCreateSerializer(**validated_data)

    def update(self, instance, validated_data):
        pass


class EventPatchSerializer(serializers.Serializer):
    eventId = serializers.CharField(max_length=255)
    calendarId = serializers.CharField(default="primary")
    summary = serializers.CharField(required=False, max_length=1000)
    description = serializers.CharField(required=False, max_length=8100)
    location = serializers.CharField(required=False, max_length=1024)
    colorId = serializers.ChoiceField(required=False, choices=[(id, id) for id in range(12)])
    attendees = EventAttendeesSerializer(required=False, many=True)
    status = serializers.ChoiceField(
        required=False, default="confirmed",
        choices=[("confirmed", "confirmed"), ("tentative", "tentative"), ("cancelled", "cancelled")])
    transparency = serializers.ChoiceField(
        required=False, default="opaque",
        choices=[("opaque", "opaque"), ("transparent", "transparent")])
    visibility = serializers.ChoiceField(
        required=False, default="default",
        choices=[("default", "default"), ("public", "public"), ("private", "private"), ("confidential", "confidential")])
    guestsCanInviteOthers = serializers.BooleanField(default=True)
    guestsCanModify = serializers.BooleanField(default=False)
    guestsCanSeeOtherGuests = serializers.BooleanField(default=True)
    reminders = EventReminderSerializer(required=False)

    def create(self, validated_data):
        return EventCreateSerializer(**validated_data)

    def update(self, instance, validated_data):
        pass


class EventDeleteSerializer(serializers.Serializer):
    eventId = serializers.CharField(max_length=255)
    calendarId = serializers.CharField(default="primary")

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class EventDateTimeCheckSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    def validate(self, data):
        if "start" and "end" in data.keys():
            if data["start"] > data["end"]:
                raise serializers.ValidationError("End datetime must occur after start datetime")
        return data


class EventDateCheckSerializer(serializers.Serializer):
    start = serializers.DateField()
    end = serializers.DateField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    def validate(self, data):
        if data["start"] > data["end"]:
            raise serializers.ValidationError("End date must occur after start date")
        return data


class StartDateCheckSerializer(serializers.Serializer):
    start = serializers.DateField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class EndDateCheckSerializer(serializers.Serializer):
    end = serializers.DateField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class StartDateTimeCheckSerializer(serializers.Serializer):
    start = serializers.DateTimeField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class EndDateTimeCheckSerializer(serializers.Serializer):
    end = serializers.DateTimeField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class TemicateEventUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'email', 'phone',)


class EventTimeSlotSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(many=False, read_only=True)
    voted_users = TemicateEventUserSerializer(many=True, read_only=True)

    class Meta:
        model = EventTimeSlot
        fields = ('id', 'start', 'end', 'votes', 'event', 'voted_users')

    def validate(self, data):
        if "start" in data.keys() and "end" in data.keys():
            if data["start"] > data["end"]:
                raise serializers.ValidationError("End must occur after start")
        return data


class EventTimeSlotVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTimeSlot
        # fields = ('id', 'start', 'end', 'votes', 'event', 'voted_users')
        fields = '__all__'
        read_only_fields = ('id', 'start', 'end', 'votes', 'event', 'voted_users')


class TemicatePollSerializer(serializers.ModelSerializer):
    event_user = TemicateEventUserSerializer(many=False)

    class Meta:
        model = TemicatePollUser
        fields = '__all__'


class TemicateEventSerializer(serializers.ModelSerializer):
    attendees = serializers.ListField(required=False, child=serializers.EmailField())
    creator = TemicateEventUserSerializer(many=False, read_only=True)
    participants = TemicateEventUserSerializer(many=True, read_only=True)
    polls = TemicatePollSerializer(many=True, read_only=True)
    event_title = serializers.CharField(required=False, max_length=1000)
    event_link = serializers.HyperlinkedIdentityField(view_name='temicate_event_detail', lookup_field='id')
    users_can_invite = serializers.BooleanField(default=False, required=False)
    users_can_modify = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = TemicateEvent
        fields = '__all__'
        ordering = ('id',)

    def validate(self, data):
        if data["start"] > data["end"]:
            raise serializers.ValidationError("End must occur after start")
        return data



class EventSerializer(serializers.ModelSerializer):
    #attendees = serializers.ListField(required=False, child=serializers.EmailField())
    #creator = TemicateEventUserSerializer(many=False, read_only=True)
    #participants = TemicateEventUserSerializer(many=True, read_only=True)
    #polls = TemicatePollSerializer(many=True, read_only=True)

    class Meta:
        model = TemicateEvent
        fields = '__all__'
        ordering = ('id',)

    def validate(self, data):
        if data["start"] > data["end"]:
            raise serializers.ValidationError("End must occur after start")
        return data

class TemicateEventEditSerializer(serializers.HyperlinkedModelSerializer):
    # attendees = serializers.ListField(required=False, child=serializers.EmailField())
    add_attendees = serializers.ListField(required=False, child=serializers.EmailField())
    del_attendees = serializers.ListField(required=False, child=serializers.EmailField())
    creator = TemicateEventUserSerializer(many=False, read_only=True)
    participants = TemicateEventUserSerializer(many=True, read_only=True)
    polls = TemicatePollSerializer(many=True, read_only=True)
    start = serializers.DateTimeField(required=False)
    end = serializers.DateTimeField(required=False)
    event_title = serializers.CharField(required=False, max_length=1000)
    event_link = serializers.HyperlinkedIdentityField(view_name='temicate_event_detail', lookup_field='id')
    users_can_invite = serializers.BooleanField(default=False, required=False)
    users_can_modify = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = TemicateEvent
        fields = ('event_title', 'event_description', 'event_activity', 'creator', 'attendees', 'participants', 'polls',
                  'voting', 'free', 'start', 'end', 'status', 'add_attendees', 'del_attendees', 'event_link', 'location',
                  'users_can_modify', 'users_can_invite')
        read_only_fields = ('voting', 'attendees', 'event_link',)
        ordering = ('id',)

    def validate(self, data):
        if "start" in data.keys() and "end" in data.keys():
            if data["start"] > data["end"]:
                raise serializers.ValidationError("End must occur after start")
        return data


class UserPollsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemicatePollUser
        fields = ('vote',)
        ordering = ('id',)


class UserReverseEventSerializer(serializers.ModelSerializer):
    attendees = serializers.ListField(child=serializers.EmailField(), read_only=True)
    creator = TemicateEventUserSerializer(many=False, read_only=True)
    participants = TemicateEventUserSerializer(many=True, read_only=True)

    class Meta:
        model = TemicateEvent
        fields = ('creator', 'participants', 'attendees', 'event_title', 'event_description',
                  'event_activity', 'location', 'free', 'voting', 'start', 'end', 'status')
        read_only_fields = ('event_title', 'event_description', 'event_activity',
                            'location', 'free', 'voting', 'start', 'end', 'status')


class UserPollsListSerializer(serializers.ModelSerializer):
    event_user = TemicateEventUserSerializer(many=False, read_only=True)
    event = UserReverseEventSerializer(many=True, read_only=True)

    class Meta:
        model = TemicatePollUser
        fields = ('id', 'vote', 'event_user', 'event', 'color', 'busy', 'notifications')
        ordering = ('id',)


class UserPollRetrieveUpdateSerializer(serializers.ModelSerializer):
    vote = serializers.ChoiceField(
        required=False,
        choices=["not_voted", "not_going", "maybe", "going"],
        error_messages={"invalid_choice": "'{input}' is not a valid choice. "
                        "You should choose one of this parameters: "
                        "'not_voted', 'not_going', 'maybe', 'going'"})
    event_user = TemicateEventUserSerializer(many=False, read_only=True)
    event = UserReverseEventSerializer(many=True, read_only=True)

    class Meta:
        model = TemicatePollUser
        fields = ('id', 'vote', 'event_user', 'event', 'color', 'busy', 'notifications')
        ordering = ('id',)
