import json
from datetime import datetime

from googleapiclient.errors import HttpError
from rest_framework import status, generics
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from accounts.models import User
from api.permissions import IsEventCreator, IsEventCreatorOrUserCanModifyEvent, \
    IsEventCreatorOrUserCanModifyTimeSlot, IsEventCreatorTimeSlot, UserPollPermissionOwner, \
    IsEventCreatorOrUserCanInvite, IsEventCreatorOrUserCanInviteOrModify
from api.serializers_specific.serlializers_events import EventCreateSerializer, EventDateTimeCheckSerializer, \
    EventDateCheckSerializer, EventPatchSerializer, StartDateCheckSerializer, StartDateTimeCheckSerializer, \
    EndDateTimeCheckSerializer, EndDateCheckSerializer, EventDeleteSerializer, CalendarEventSerializer, \
    TemicateEventSerializer, UserPollsListSerializer, UserPollRetrieveUpdateSerializer, TemicateEventEditSerializer, \
    EventTimeSlotSerializer, EventTimeSlotVoteSerializer
from api.utils.common import make_credentials,make_cred,date_from_android,get_cred
from api.utils.utils_events import update_event_voting,get_events_from_google
from api.utils.utils_freebusy import get_user_freebusy_list

from events.models import CalendarEvent, TemicateEvent, TemicatePollUser, EventTimeSlot



class TeamicateEventAddApiView(generics.ListAPIView):
    serializer_class = TemicateEventSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        data = self.request.data
        serializer = TemicateEventSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# class EventAddApiView(generics.ListAPIView):
#     # serializer_class = TemicateEventSerializer
#     permission_classes = (IsAuthenticated,)
#
#     def post(self, request, *args, **kwargs):
#         current_user = self.request.auth.user
#         data = self.request.data
#         serializer = TemicateEventSerializer(data=data)
#         if serializer.is_valid():
#             serializer.save()
#             return JsonResponse(serializer.data, status=201)
#         return JsonResponse(serializer.errors, status=400)
#
#


class CalendarEventListApiView(generics.ListAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = CalendarEvent.objects.filter(calendar__user=self.request.auth.user)
        return queryset


class EventsListApiView(generics.ListAPIView):
    '''
     get all events list - teamicate + google + maybe other
    '''
    serializer_class = CalendarEventSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = CalendarEvent.objects.filter(calendar__user=self.request.auth.user)
        return queryset


class CalendarEventSyncApiView(generics.ListAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = CalendarEvent.objects.all()

    def get(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        items = make_credentials(request=self.request, user=current_user, events=True)
        if "error" in items:
            return Response(items, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(items, status=status.HTTP_200_OK)

class CalendarEventFromGoogle(generics.ListAPIView):
    '''
     get user events from google  - TO DO !
    '''
    serializer_class = CalendarEventSerializer
    permission_classes = (IsAuthenticated,)
    queryset = CalendarEvent.objects.all()

    def get(self, request, *args, **kwargs):
        # TO DO: change for multiple google accoutns of user
        current_user = self.request.auth.user
        # items = make_credentials(request=self.request, user=current_user, events=True)
        # events_list = []
        email = self.request.auth.user.email
        # http, res = make_cred(self.request, current_user, email)
        http, res = get_cred(current_user, email, flow=None)
        if http is not None:
            print('Get events from google')
            # TO DO : do time parameters for query
            items = get_events_from_google (current_user, None, None, None, http)

        if "error" in items:
            return Response(items, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(items, status=status.HTTP_200_OK)


class CalendarEventDetailApiView(generics.RetrieveAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "event_id"

    def get_queryset(self):
        queryset = CalendarEvent.objects.filter(event_id=self.kwargs["event_id"])
        return queryset




class EventsAPIView(GenericAPIView):
    """
    post:
    Create a new CalendarEvent instance
    <key> <value>
    headers: <Authorization> <Token 123456789token123456789> use token from registration
    query params: <code> <value> use code from redirect of Google OAuth2.0
    body:
    {
    ===== required =====
    "start": {"date": "YYYY-MM-DD" or "dateTime": "YYYY-MM-DDThh:mm:ss+hh:mm"},
    ??? where +hh:mm / -hh:mm -- it's timeZone difference from UTC (Example: "2018-05-23T10:00:00+03:00")  [ISO 8601]
    "end": {"date": "YYYY-MM-DD" or "dateTime": "YYYY-MM-DDThh:mm:ss+hh:mm"},
    ??? where +hh:mm / -hh:mm -- it's timeZone difference from UTC (Example: "2018-05-23T10:00:00+03:00")  [ISO 8601]
    additional: must be after the start
    ===== optional =====
    "calendarId": "<ID>", -- by default it's "primary"
    "summary": "<Title of event>",
    "description": "<Description of event>",
    "attendees": [{"email": "<example@gmail.com>"}, {"email": "<example2@gmail.com>"}],
    "reminders": {
        "useDefault": false,
        "overrides": [{"method": "popup","minutes": <10>},{"method": "email","minutes": <10>}]
    }
    ??? there are two methods inside overrides: <popup> | <email> and value of minutes from 0 to 40320 (4 weeks)
    "guestsCanModify": false,
    "guestsCanInviteOthers": true,
    "guestsCanSeeOtherGuests": true,
    """
    # permission_classes = (IsAuthenticated,)
    serializer_class = EventCreateSerializer

    def post(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        service = make_credentials(request=request, user=current_user, to_google=True)
        # get start and end from request.data and validate it with Date / DateTime serializers
        dates = self.check_dates_from_request(data=request.data)
        if type(dates) is Response:
            return dates
        # make filtered request.data without start and end to validate it
        filtered_data = self.cut_dates_from_request(data=request.data)
        # validating filtered_data via serializer
        serializer = EventCreateSerializer(data=filtered_data)
        return self.make_API_call(request, serializer, service)

    def patch(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        service = make_credentials(request=request, user=current_user, to_google=True)
        dates = self.check_dates_from_request(data=request.data, partial=True)
        if type(dates) is Response:
            return dates
        filtered_data = self.cut_dates_from_request(data=request.data)
        serializer = EventPatchSerializer(data=filtered_data)
        return self.make_API_call(request, serializer, service)

    def delete(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        service = make_credentials(request=request, user=current_user, to_google=True)
        serializer = EventDeleteSerializer(data=request.data)
        return self.make_API_call(request, serializer, service)

    def check_dates_from_request(self, data, partial=False):
        check_data = {}
        start = False
        end = False
        if partial:
            try:
                start = data["start"]
            except KeyError:
                pass
            try:
                end = data["end"]
            except KeyError:
                pass
            if start:
                if "dateTime" in start.keys():
                    check_data["start"] = start["dateTime"]
                    serializer = StartDateTimeCheckSerializer(data=check_data)
                    return serializer.is_valid(raise_exception=True)
                if "date" in start.keys():
                    check_data["start"] = start["date"]
                    serializer = StartDateCheckSerializer(data=check_data)
                    return serializer.is_valid(raise_exception=True)
            elif end:
                if "dateTime" in end.keys():
                    check_data["end"] = end["dateTime"]
                    serializer = EndDateTimeCheckSerializer(data=check_data)
                    return serializer.is_valid(raise_exception=True)
                if "date" in end.keys():
                    check_data["end"] = end["date"]
                    serializer = EndDateCheckSerializer(data=check_data)
                    return serializer.is_valid(raise_exception=True)
            elif end and start:
                if "dateTime" in (start.keys() or end.keys()) and "date" not in (start.keys() and end.keys()):
                    if "dateTime" in start.keys():
                        check_data["start"] = start["dateTime"]
                    if "dateTime" in end.keys():
                        check_data["end"] = end["dateTime"]
                    serializer = EventDateTimeCheckSerializer(data=check_data, partial=False)
                    return serializer.is_valid(raise_exception=True)
                elif "date" in (start.keys() or end.keys()) and "dateTime" not in (start.keys() and end.keys()):
                    if "date" in start.keys():
                        check_data["start"] = start["date"]
                    if "date" in end.keys():
                        check_data["end"] = end["date"]
                    serializer = EventDateCheckSerializer(data=check_data, partial=False)
                    return serializer.is_valid(raise_exception=True)
                else:
                    return Response({"error": "Start and end times must either both be date or both be dateTime."})
        else:
            try:
                start = (data["start"])
                end = (data["end"])
            except KeyError:
                return Response({"error": "You should provide start and end"})
            if "dateTime" in (start.keys() and end.keys()):
                check_data["start"] = start #start["dateTime"]
                check_data["end"] = end # end["dateTime"]
                serializer = EventDateTimeCheckSerializer(data=check_data)
                return serializer.is_valid(raise_exception=True)
            elif "date" in (start.keys() and end.keys()):
                check_data["start"] = start["date"]
                check_data["end"] = end["date"]
                serializer = EventDateCheckSerializer(data=check_data)
                return serializer.is_valid(raise_exception=True)
            else:
                return Response({"error": "Start and end times must either both be date or both be dateTime."})

    def cut_dates_from_request(self, data):
        filtered_data = {}
        filter_keys = ["start", "end"]
        for key, value in data.items():
            if key in filter_keys:
                pass
            else:
                filtered_data[key] = value
        return filtered_data

    def make_API_call(self, request, serializer, service):
        if serializer.is_valid(raise_exception=True):
            # print("Valid")
            # print("Data: ", serializer.data)
            # print("Validated data: ", serializer.validated_data)
            try:
                if "google access url" in service.keys():
                    return Response(service, status.HTTP_200_OK)
                if "error" in service.keys():
                    return Response(service, status.HTTP_400_BAD_REQUEST)
            except AttributeError:
                if request.method == "POST":
                    try:
                        request_and_response = service.events().insert(
                            calendarId=request.data["calendarId"],
                            body=request.data).execute()
                        return Response(request_and_response, status.HTTP_201_CREATED)
                    except KeyError:
                        return Response({"error": "calendarId required"}, status.HTTP_400_BAD_REQUEST)
                    except HttpError as error:
                        return Response(json.loads(error.content), status.HTTP_400_BAD_REQUEST)
                elif request.method == "PATCH":
                    try:
                        request_and_response = service.events().patch(
                            calendarId=request.data["calendarId"],
                            eventId=request.data["eventId"],
                            body=request.data).execute()
                        return Response(request_and_response, status.HTTP_200_OK)
                    except KeyError:
                        return Response({"error": "calendarId and eventId required"}, status.HTTP_400_BAD_REQUEST)
                    except HttpError as error:
                        return Response(json.loads(error.content), status.HTTP_400_BAD_REQUEST)
                elif request.method == "DELETE":
                    try:
                        request_and_response = service.events().delete(
                            calendarId=request.data["calendarId"], eventId=request.data["eventId"]).execute()
                        return Response(request_and_response, status.HTTP_200_OK)
                    except KeyError:
                        return Response({"error": "calendarId and eventId required"}, status.HTTP_400_BAD_REQUEST)
                    except HttpError as error:
                        return Response(json.loads(error.content), status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"error": "method not allowed"}, status.HTTP_405_METHOD_NOT_ALLOWED)
        else:
            return Response({"error": "this error never be"}, status.HTTP_400_BAD_REQUEST)
            # print("Not valid")
            # print("Errors: ", serializer.errors)


class TemicateEventAPIView(generics.ListCreateAPIView):
    serializer_class = TemicateEventSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = TemicateEvent.objects.filter(creator=self.request.auth.user)
        return queryset

    def perform_create(self, serializer):
        # set for creator current user
        serializer.validated_data["creator"] = self.request.auth.user
        # make free_list by start date day with sync before
        serializer.validated_data["free"] = get_user_freebusy_list(
            request=self.request, user=self.request.auth.user,
            day=serializer.validated_data["start"].date(), sync_before=True, convert_free=True
        )
        # check if user make a list of emails to current event
        if serializer.validated_data["attendees"]:
            # get user objects from list of emails
            user_list = self.catch_users_from_attendees(attendees=serializer.validated_data["attendees"])
            user_list.append(self.request.auth.user)
            # if user object in list
            if user_list:
                # set the users object for participants of current event
                serializer.validated_data["participants"] = user_list
                # save the event into DB
                instance = serializer.save()
                # iterate for every user object in list
                for user in user_list:
                    # make the poll for event with user in iteration
                    poll = TemicatePollUser(event_user=user)
                    # save the object to DB
                    poll.save()
                    # add reverse relationship to event id
                    poll.event.add(instance.id)
        else:
            poll = TemicatePollUser(event_user=self.request.auth.user)
            poll.save()
            serializer.validated_data["participants"] = [self.request.auth.user]
            instance = serializer.save()
            poll.event.add(instance.id)

    def catch_users_from_attendees(self, attendees):
        user_list = []
        # iterate through the list of emails
        for email in attendees:
            # try to find the user in DB by email
            try:
                user_list.append(User.objects.get(email=email))
            except:
                pass
        # return the list of found users objects
        return user_list

    def get(self, request, *args, **kwargs):
        update_event_voting(user=self.request.auth.user)
        return self.list(request, *args, **kwargs)


class TemicateEventRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TemicateEventEditSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['delete', 'get', 'put']
    # http_method_names = ['patch', 'delete', 'get', 'put']
    lookup_field = "id"
    queryset = TemicateEvent.objects.all()

    def get_permissions(self):
        if self.request.method == "GET":
            return (IsAuthenticated(),)
        elif self.request.method == "PUT":
            # return (IsAuthenticated(), IsEventCreatorOrUserCanInvite(), IsEvedatetime.fromtimestamp(int("1284101485"))ntCreatorOrUserCanModifyEvent(),)
            return (IsAuthenticated(), IsEventCreatorOrUserCanInviteOrModify(),)
        elif self.request.method == "DELETE":
            return (IsAuthenticated(), IsEventCreator(),)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # synchronize voting for only this instance
        update_event_voting(user=self.request.auth.user, event_id=instance.id)
        # update instance after synchronization
        instance = self.get_object()
        # get updated_serializer
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # def patch(self, request, *args, **kwargs):
    #     return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        # check if add_attendees list appended to query
        try:
            if serializer.validated_data["add_attendees"]:
                # iterate through the add_attendees list
                for attendee in serializer.validated_data["add_attendees"]:
                    # catch email and if it is locating there, pass it
                    if attendee in serializer.instance.attendees:
                        pass
                    else:
                        try:
                            # get instance of user by email
                            user_from_email = User.objects.get(email=attendee)
                            # creating new poll for this user instance
                            poll = TemicatePollUser(event_user=user_from_email)
                            # save the object to DB
                            poll.save()
                            # add reverse relationship to event id
                            poll.event.add(serializer.instance.id)
                            # add user to participants for current event
                            serializer.instance.participants.add(user_from_email)
                        except:
                            # if user doesn't exist in DB
                            pass
                        # append this email to instance to list of attendees
                        serializer.instance.attendees.append(attendee)
        except KeyError:
            # pass if list weren't provided in query
            pass
        # check if del_attendees list appended to query
        try:
            if serializer.validated_data["del_attendees"]:
                # iterate through the del_attendees list
                for attendee in serializer.validated_data["del_attendees"]:
                    # check if email is locating in current instance inside list of attendees
                    if attendee in serializer.instance.attendees:
                        try:
                            # catch user from DB by email
                            user_from_email = User.objects.get(email=attendee)
                            # delete poll instance, where has relations to caught user
                            # and event is current event instance
                            TemicatePollUser.objects.filter(event_user=user_from_email,
                                                            event=serializer.instance).delete()
                            # delete relation from this user and event instance
                            serializer.instance.participants.remove(user_from_email)
                        except:
                            # if user isn't locating in current instance inside list of attendees
                            pass
                        # delete email from list of attendees
                        serializer.instance.attendees.remove(attendee)
                    # catch email and if it isn't locating there, pass it
                    else:
                        pass
        except KeyError:
            # pass if list weren't provided in query
            pass
        # check if start or end inside query
        try:
            if serializer.validated_data["start"] or serializer.validated_data["end"]:
                # get all polls, where have relation to current instance event
                polls = TemicatePollUser.objects.filter(event=serializer.instance)
                # iterate through the polls and reset vote to "not_voted" (with saving the instance)
                for poll in polls:
                    poll.vote = "not_voted"
                    poll.save()
        except KeyError:
            # pass if "start" or "end" weren't provided in query
            pass
        # check if "start" in query
        try:
            if serializer.validated_data["start"]:
                # make free_list by start date day with sync before and put it inside the "free" of instance
                serializer.validated_data["free"] = get_user_freebusy_list(
                    request=self.request, user=self.request.auth.user,
                    day=serializer.validated_data["start"].date(), sync_before=True, convert_free=True
                )
        except KeyError:
            # pass if "start" wasn't provided in query
            pass
        # make update for voting for current event instance
        update_event_voting(user=self.request.auth.user, event_id=serializer.instance.id)

        serializer.instance.save()

        if "users_can_invite" in self.request.data.keys():
            serializer.instance.users_can_invite = serializer.validated_data["users_can_invite"]
        else:
            serializer.validated_data["users_can_invite"] = serializer.instance.users_can_invite
            serializer.instance.users_can_invite = serializer.validated_data["users_can_invite"]
        if "users_can_modify" in self.request.data.keys():
            serializer.instance.users_can_modify = serializer.validated_data["users_can_modify"]
        else:
            serializer.validated_data["users_can_modify"] = serializer.instance.users_can_modify
            serializer.instance.users_can_modify = serializer.validated_data["users_can_modify"]

        # get updated instance for current event
        serializer.instance = TemicateEvent.objects.get(id=serializer.instance.id)
        # save and return new instance
        serializer.save()

    def perform_destroy(self, instance):
        # delete all polls with relation to this event
        TemicatePollUser.objects.filter(event=instance).delete()
        # delete all timeslots with relation to this event
        EventTimeSlot.objects.filter(event=instance).delete()
        # delete this event
        instance.delete()

# class EventFilter(filters.FilterSet):
#     start_gte = filters.DateTimeFilter(name="start", lookup_expr='gte')
#     #start_lte = filters.DateTimeFilter(name="start", lookup_expr='lte')
#     #end_gte = filters.DateTimeFilter(name="end", lookup_expr='gte')
#     end_lte = filters.DateTimeFilter(name="end", lookup_expr='lte')
#
#     class Meta:
#         model = TemicateEvent
#         fields = ['start_gte','end_lte']


class TemicateEventsListAPIView(generics.ListAPIView):
    # get all teamicate events for current user
    permission_classes = (IsAuthenticated,)
    queryset = TemicateEvent.objects.all()
    serializer_class = TemicateEventSerializer

    def get_queryset(self):
        # current_user = self.request.auth.user
        query =  ['creator_id = %s']
        params = [self.request.auth.user.pk]
        queryset = TemicateEvent.objects.extra(where=query, params=params)
        return queryset


class EventsByFilterAPIView(generics.ListAPIView):
    # filter parameters:
    permission_classes = (IsAuthenticated,)
    queryset = TemicateEvent.objects.all()
    serializer_class = TemicateEventSerializer

    #def get_queryset(self):
    def get (self, *args, **kwargs):
        events = {}
        # current_user = self.request.auth.user
        df = self.request.query_params.get('fromdate',None)
        dt =  self.request.query_params.get('todate',None)
        if df and dt:
            date_from = date_from_android(int(df))
            date_to = date_from_android(int(dt))
            print('Date_from',date_from, type(date_from))
            print('Date_to', date_to, type(date_to))
            query  =['creator_id = %s and "start" >= %s and "end"<=%s']
            params =[self.request.auth.user.pk, date_from,date_to]
        else:
            query =  ['creator_id = %s']
            params = [self.request.auth.user.pk]

        queryset = TemicateEvent.objects.extra(where=query, params=params)
        events['teamicate_events'] = queryset
        email = user=self.request.user.email
        # http, res = make_cred(self.request, self.request.user,email,flow=None)
        http, res = get_cred(self.request.user, email, flow=None)

        if http is not None:
            print('Get events from google')
            # TO DO : do time parameters for query
            items = get_events_from_google(self.request.user, date_from, date_to, None, http)
            events['google_events'] = items

        return Response(events, status=200)



class UserPollsListAPIView(generics.ListAPIView):
    serializer_class = UserPollsListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = TemicatePollUser.objects.filter(event_user=self.request.auth.user)
        for poll in queryset:
            # make update for voting for current event instance
            update_event_voting(user=self.request.auth.user, event_id=poll.event.get().id)
        queryset = TemicatePollUser.objects.filter(event_user=self.request.auth.user)
        return queryset


class UserPollRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserPollRetrieveUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == "GET":
            return (IsAuthenticated(), UserPollPermissionOwner(),)
        elif self.request.method == "PUT":
            return (IsAuthenticated(), UserPollPermissionOwner(),)
        elif self.request.method == "PATCH":
            return (IsAuthenticated(), UserPollPermissionOwner(),)

    def get_queryset(self):
        queryset = TemicatePollUser.objects.filter(event_user=self.request.auth.user)
        for poll in queryset:
            # make update for voting for current event instance
            update_event_voting(user=self.request.auth.user, event_id=poll.event.get().id)
        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_update(self, serializer):
        # make update for voting for current poll instance
        update_event_voting(user=self.request.auth.user,
                            event_id=serializer.instance.event.get().id)
        # get updated instance for current poll
        serializer.instance = TemicatePollUser.objects.get(id=serializer.instance.id)
        # save and return new instance
        serializer.save()


class EventTimeSlotRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EventTimeSlotSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "id"

    def get_permissions(self):
        if self.request.method == "GET":
            return (IsAuthenticated(),)
        elif self.request.method == "PUT":
            return (IsAuthenticated(), IsEventCreatorOrUserCanModifyTimeSlot(),)
        elif self.request.method == "PATCH":
            return (IsAuthenticated(), IsEventCreatorOrUserCanModifyTimeSlot(),)
        elif self.request.method == "DELETE":
            return (IsAuthenticated(), IsEventCreatorTimeSlot(),)

    def get_queryset(self):
        queryset = EventTimeSlot.objects.filter(event_id=self.kwargs['event_id'])
        return queryset

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        instance.delete()


class EventTimeSlotListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = EventTimeSlotSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == "GET":
            return (IsAuthenticated(),)
        elif self.request.method == "POST":
            return (IsAuthenticated(), IsEventCreatorOrUserCanModifyTimeSlot(),)

    def get_queryset(self):
        queryset = EventTimeSlot.objects.filter(event_id=self.kwargs["event_id"])
        return queryset

    def perform_create(self, serializer):
        serializer.validated_data["event_id"] = self.kwargs["event_id"]
        serializer.save()

class TimeSlotCreateAPIView(generics.ListCreateAPIView):
    serializer_class = EventTimeSlotSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == "GET":
            return (IsAuthenticated(),)
        elif self.request.method == "POST":
            return (IsAuthenticated(), IsEventCreatorOrUserCanModifyTimeSlot(),)

    def perform_create(self, serializer):
        serializer.validated_data["event_id"] = self.request.data["event"]
        serializer.save()


class EventTimeSlotVoteAPIView(generics.ListCreateAPIView):
    serializer_class = EventTimeSlotVoteSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "id"

    def get_queryset(self):
        queryset = EventTimeSlot.objects.filter(event_id=self.kwargs["event_id"])
        return queryset

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        # get all participants of event
        participants = TemicateEvent.objects.get(id=self.kwargs["event_id"]).participants
        # check if user inside the participants
        can_vote = participants.filter(email=self.request.auth.user.email).exists()
        if can_vote:
            # get current timeslot by id in url
            current_timeslot = EventTimeSlot.objects.get(id=self.kwargs["id"])
            # check if user already voted, clean the vote from this user
            if self.request.auth.user in current_timeslot.voted_users.all():
                # clean the one vote from user
                current_timeslot.votes -= 1
                # remove all relations from current timeslot and this user
                current_timeslot.voted_users.remove(self.request.auth.user.id)
                # save changes
                current_timeslot.save()
            # if user not already voted
            else:
                # make the vote from this one
                current_timeslot.votes += 1
                # add relations from user to this timeslot
                current_timeslot.voted_users.add(self.request.auth.user.id)
                # save changes
                current_timeslot.save()
        # update an instance of timeslot
        serializer.instance = EventTimeSlot.objects.get(id=self.kwargs["id"])
        # save an instance to database
        serializer.save()

