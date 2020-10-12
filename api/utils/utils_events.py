from googleapiclient.discovery import build
import datetime

from calendars.models import UserCalendars
from events.models import CalendarEvent, TemicateEvent


def create_events_from_api(user, http=None):
    # build the API service to calendar v3 with authorized credentials
    service = build('calendar', 'v3', http=http)
    # make complete flow to create / update / delete info in calendars
    # create_calendars_from_api(user, http=http)
    # get calendars ids of current user
    user_calendars_ids = UserCalendars.objects.filter(user=user).values('calendar_id')
    # create list to store events ids of user's calendars
    list_of_user_events_ids = []
    # create dict to store events data from API call
    real_events_dict = {}
    # iteration through all calendars ids of current user
    for calendar_id in user_calendars_ids:
        # get all events ids by calendar_id
        user_events_id = CalendarEvent.objects.filter(calendar__calendar_id=calendar_id["calendar_id"]).values("event_id")
        # insert events ids into list_of_user_events_ids
        list_of_user_events_ids.append(user_events_id)
        # make query to Google calendar.events v3 API and execute() it to the dictionary
        calendar_list = service.events().list(calendarId=calendar_id["calendar_id"]).execute()
        # print(calendar_list['items'])
        # add item to dict with calendar id for KEY and dict of events for VALUE
        real_events_dict[calendar_id["calendar_id"]] = calendar_list["items"]

    # check_ids(real_events_dict, list_of_user_events_ids)

    return real_events_dict



def get_events_from_google (user, date_from=None, date_to=None, calendar_id=None, http=None):
    # build the API service to calendar v3 with authorized credentials
    # http must be obtained from make_cred
    query = {
        "calendarId": "primary" if calendar_id is None else calendar_id,
    }

    if date_from:
        query['timeMin'] = date_from.isoformat() + 'Z'  # 'Z' indicates UTC time

    if date_to:
        query['timeMax'] = date_to.isoformat() + 'Z'  # 'Z' indicates UTC time

    service = build('calendar', 'v3', http=http)
    # query['calendarId'] = 'primary'
    query['singleEvents'] = True
    query['orderBy'] = 'startTime'
    eventsResult = service.events().list(**query).execute()
    items = eventsResult.get('items', [])
    events =[]
    for item in items:
        event = gevent_to_teamicate(item, cut_id=True)
        events.append(event)
    return events






def check_ids(real_events_dict, user_calendars_events):
    real_ids_list = []
    current_ids_list = []
    list_to_create = []
    list_to_update = []
    list_to_delete = []
    # iteration through the api response dict with scoped calendars
    for calendar in real_events_dict.values():
        for event in calendar:
            real_ids_list.append(event['id'])
    # iteration through user calendars and take calendar_id
    for calendar in user_calendars_events:
        for event in calendar:
            current_ids_list.append(event['event_id'])
    # iteration through real_ids_list to make create or update
    for event_id in real_ids_list:
        # check that calendar_id inside current_id_list
        if event_id in current_ids_list:
            list_to_update.append(event_id)
        else:
            list_to_create.append(event_id)
    # iteration through current_ids_list to make delete
    for event_id in current_ids_list:
        # check that calendar_id not inside real_ids_list
        if event_id not in real_ids_list:
            list_to_delete.append(event_id)
    return make_updates(real_events_dict, list_to_create, list_to_update, list_to_delete)


def make_updates(items_dict=None, list_to_create=None,
                 list_to_update=None, list_to_delete=None):
    if list_to_delete:
        delete_query = CalendarEvent.objects.filter(event_id__in=list_to_delete)
        if delete_query.exists():
            delete_query.delete()
    if list_to_create:
        if len(list_to_create) == 1:
            for calendar_id, calendar in items_dict.items():
                for event in calendar:
                    if event['id'] in list_to_create:
                        kwargs = create_event_kwargs(event)
                        current_calendar = UserCalendars.objects.get(calendar_id=calendar_id)
                        CalendarEvent.objects.create(calendar=current_calendar, **kwargs)
        else:
            bulk_create_list = []
            for calendar_id, calendar in items_dict.items():
                for event in calendar:
                    if event['id'] in list_to_create:
                        kwargs = create_event_kwargs(event)
                        current_calendar = UserCalendars.objects.get(calendar_id=calendar_id)
                        bulk_create_list.append(CalendarEvent(calendar=current_calendar, **kwargs))
            CalendarEvent.objects.bulk_create(bulk_create_list)
    # TODO: optimize update queries to DB
    if list_to_update:
        for item in items_dict.values():
            for event in item:
                if event['id'] in list_to_update:
                    kwargs = create_event_kwargs(event, cut_id=True)
                    CalendarEvent.objects.filter(event_id=event['id']).update(**kwargs)
    return None


def gevent_to_teamicate(event, cut_id=False):
    # list of values to cut from kwargs

    ''' filed in db:
     event_title text NOT NULL,
  event_activity text,
  event_description text,
  location character varying(1024),
  attendees jsonb,
  voting jsonb,
  free jsonb,
  start timestamp with time zone NOT NULL,
  "end" timestamp with time zone NOT NULL,
  status character varying(25) NOT NULL,
  users_can_modify boolean NOT NULL,
  users_can_invite boolean NOT NULL,
  creator_id integer NOT NULL,
  event_end timestamp with time zone,
  event_start timestamp with time zone,
     ---------------------------------------

    :param event:
    :param cut_id:
    :return:
    '''
    not_needed_keys = ['kind', 'etag', 'sequence','iCalUID', 'extendedProperties', 'recurringEventId', 'originalStartTime']
    # add renamed id (event_id) to list
    if cut_id is True:
        not_needed_keys.append('event_id')
    # dictionary of keys with old_name: renamed_name to use with CalendarEvent model
    renamed_keys = {
        'id': 'event_id', 'summary': 'event_title', 'description': 'event_description',
        'htmlLink': 'html_link', 'guestsCanModify': 'guest_can_modify', 'guestsCanInviteOthers': 'guest_can_invite',
        'guestsCanSeeOtherGuests': 'guest_can_see_others', 'colorId': 'color_id',
    }
    kwargs = {}
    for key, value in event.items():
        # if the key from event iteration located in renamed_keys
        if key in renamed_keys.keys():
            # use renamed key name for this value
            kwargs[renamed_keys[key]] = value
        # otherwise use default key name for this value
        else:
            kwargs[key] = value
    for key in not_needed_keys:
        if key in kwargs.keys():
            # cut key from kwargs
            kwargs.pop(key)
    # print(kwargs)
    return kwargs

def create_event_kwargs(event, cut_id=False):
    # list of values to cut from kwargs
    not_needed_keys = ['kind', 'etag', 'iCalUID', 'extendedProperties', 'recurringEventId', 'originalStartTime']
    # add renamed id (event_id) to list
    if cut_id is True:
        not_needed_keys.append('event_id')
    # dictionary of keys with old_name: renamed_name to use with CalendarEvent model
    renamed_keys = {
        'id': 'event_id', 'summary': 'event_title', 'description': 'event_description',
        'htmlLink': 'html_link', 'guestsCanModify': 'guest_can_modify', 'guestsCanInviteOthers': 'guest_can_invite',
        'guestsCanSeeOtherGuests': 'guest_can_see_others', 'colorId': 'color_id',
    }
    kwargs = {}
    for key, value in event.items():
        # if the key from event iteration located in renamed_keys
        if key in renamed_keys.keys():
            # use renamed key name for this value
            kwargs[renamed_keys[key]] = value
        # otherwise use default key name for this value
        else:
            kwargs[key] = value
    for key in not_needed_keys:
        if key in kwargs.keys():
            # cut key from kwargs
            kwargs.pop(key)
    # print(kwargs)
    return kwargs


def update_event_voting(user, event_id=None):
    if event_id:
        event = TemicateEvent.objects.get(id=event_id)
        update_polls(event=event)
    else:
        queryset = TemicateEvent.objects.filter(creator=user)
        for event in queryset:
            update_polls(event=event)


def update_polls(event):
    poll_dict = {}
    for poll in event.polls.all():
        poll_dict[poll.event_user_id] = poll.vote
    event.voting = poll_dict
    event.save()
    return event

def create_event (user, data):
    '''
    :param user - authenticated user
    :param data: json data for insert :
     data for insert into event,
                          participant,
                          time_slot,
                          suggested_date_settings
    :return: 
    '''

    event = {
        "id": data["id"] or 0,
        "attendees": {[]},
        "creator": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "phone": user.phone
        },
        "participants": {[]},
        "polls": [],
        "event_title": data["event_title"],
        "event_activity": data["event_activity"],
        "event_description": data["event_description"],
        "location": data["location"],
        "voting": {},
        "free": [
            {
                "end": "2018-07-30T10:00:10",
                "start": "2018-07-30T22:00:00"
            }
        ],
        "start": data["start"],
        "end": data["end"],
        "status": data["status"],
        "users_can_modify": data["users_can_modify"],
        "users_can_invite": data["users_can_invite"]
    }
    if event_id==0:
        n = TemicateEvent.objects.create(creator_id = user.pk, event_title=data["event_title"],event_activity =data["event_activity"],
                                         event_description=data["event_description"],location=data["location"], start=data["start"],
                                         end= data["end"],status=data["status"],users_can_modify=data["users_can_modify"],
                                         users_can_invite=data["users_can_invite"])
        n.save()
        event["id"] = n.pk
        event["result"]["status"] = 'Insert new record in DB'
    else:
        co = TemicateEvent.objects.filter(id=calendar_id)
        co.update(creattor_id = user.pk, evemt_title=data["event_title"],event_activity =data["event_activity"],
                                         event_description=data["event_description"],location=data["location"], start=data["start"],
                                         end= data["end"],status=data["status"],users_can_modify=data["users_can_modify"],
                                         users_can_invite=data["users_can_invite"])
        event["result"]["status"] = 'Update calendar in DB'



    return event
