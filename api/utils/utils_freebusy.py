import json
import datetime

from django.utils import timezone
from googleapiclient.discovery import build

from accounts.models import User
from events.models import UserFreeBusy
from outbizzed.settings.base import FREEBUSY_DAYS_PERIOD
from calendars.models import UserCalendars

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

def create_freebusy_from_api(user, http=None):
    # build the API service to calendar v3 with authorized credentials
    service = build('calendar', 'v3', http=http)
    # get calendars ids of current user
    user_calendars_ids = UserCalendars.objects.filter(user=user).values('calendar_id')
    # calendars_id_list = [calendar_id for calendar_id in user_calendars_ids]
    list_of_calendars_ids = []
    for calendar_id in user_calendars_ids:
        for value in calendar_id.values():
            list_of_calendars_ids.append({"id": value})
    body = {
        "items": [item for item in list_of_calendars_ids],
        "timeMin": timezone.now().isoformat(),
        "timeMax": (timezone.now()+timezone.timedelta(days=FREEBUSY_DAYS_PERIOD)).isoformat()
    }
    real_freebusy = service.freebusy().query(body=body).execute()
    update_freebusy(user, real_freebusy)
    return real_freebusy

# def get_freebusy_from_api(user, http=None):
#     # build the API service to calendar v3 with authorized credentials
#     service = build('calendar', 'v3', http=http)
#     # get calendars ids of current user
#     calendar_list = UserCalendars.objects.filter(user=user,provider = 'google').values('id')
#     user_layers_ids = UserCalendarLayer.objects.filter(calendar_id_in = calendar_list).values('ids')
#     # calendars_id_list = [calendar_id for calendar_id in user_calendars_ids]
#     list_of_kayer_ids = []
#     for layer_id in user_layers_ids:
#         for value in calendar_id.values():
#             list_of_calendars_ids.append({"id": value})
#     body = {
#         "items": [item for item in list_of_calendars_ids],
#         "timeMin": timezone.now().isoformat(),
#         "timeMax": (timezone.now()+timezone.timedelta(days=FREEBUSY_DAYS_PERIOD)).isoformat()
#     }
#     real_freebusy = service.freebusy().query(body=body).execute()
#     update_freebusy(user, real_freebusy)
#     return real_freebusy



def update_freebusy(user, real_freebusy):
    kwargs = create_freebusy_kwargs(real_freebusy)
    UserFreeBusy.objects.update_or_create(user=user, defaults=kwargs)


def create_freebusy_kwargs(real_freebusy):
    not_needed_keys = ["kind", "timeMin", "timeMax"]
    renamed_keys = {"calendars": "busy", }
    kwargs = {}
    # generate kwargs with filter to not_needed_keys
    for key, value in real_freebusy.items():
        if key not in not_needed_keys:
            # rename key if it inside the renamed_keys dict
            if key in renamed_keys.keys():
                kwargs[renamed_keys[key]] = value
    # make an empty list to filter empty busy in calendars
    clear_from_kwargs = []
    for key, value in kwargs["busy"].items():
        # if busy is not empty in kwargs -> calendar
        if value["busy"]:
            pass
        else:
            # append key to filter list
            clear_from_kwargs.append(key)
    # iterate through filter list
    for calendar in clear_from_kwargs:
        # delete empty calendar from kwargs
        kwargs["busy"].pop(calendar)
    return kwargs


def get_user_freebusy_list(request, user, day, sync_before=False, convert_free=False):
    if sync_before:
        # make sync for Google Calendar v3 (FreeBusy->query)
        from api.utils.common import make_credentials
        make_credentials(request=request, user=user, freebusy=True)
    # get updated user object
    updated_user = User.objects.get(id=user.id)
    return_busy_list = []
    # iteration through the user busy dict
    for busy in updated_user.userfreebusy.busy.values():
        # iteration through the busy item
        for busy_list in busy.values():
            # iteration through the period in calendar busy_list
            for date_time_period in busy_list:
                # check is "start" exist in every dict item
                if "start" in date_time_period.keys():
                    # convert string iso datetime into python datetime
                    start_datetime_from_string = datetime.datetime.strptime(date_time_period["start"], DATETIME_FORMAT)
                    # check if day being in the right time interval (from 00:00:00 current day TO 00:00:00 next day)
                    if start_datetime_from_string.date() <= day < \
                            (start_datetime_from_string.date() + datetime.timedelta(days=1)):
                        # if it's right, convert "end" string to python datetime
                        end_datetime_from_string = datetime.datetime.strptime(date_time_period["end"], DATETIME_FORMAT)
                        # add the dict {"start": datetime, "end": datetime} to return_busy_list
                        return_busy_list.append({"start": start_datetime_from_string,
                                                 "end": end_datetime_from_string})
    # get all event instances which confirmed and event's datetime start|end located inside the time slot
    confirmed_events = updated_user.event.filter(
        status="confirmed",
        #start__gte=datetime.datetime.combine(day, datetime.time(00, 00), tzinfo=timezone.utc),
        #end__lte=datetime.datetime.combine(day+datetime.timedelta(days=1), datetime.time(00, 00), tzinfo=timezone.utc)
        start__gte = datetime.datetime.combine(day, datetime.time(00, 00)),
        end__lte = datetime.datetime.combine(day + datetime.timedelta(days=1), datetime.time(00, 00))
    )
    # iterate through this events
    for event in confirmed_events:
        # if user chose busy for this event
        if event.polls.get(event_user=updated_user).busy:
            # normalize datetime from YYYY-MM-DDThh:mm:ss:uuuuuu+00:00 TO YYYY-MM-DDThh:mm:ssZ"
            start = datetime.datetime.strptime(event.start.strftime(DATETIME_FORMAT), DATETIME_FORMAT)
            end = datetime.datetime.strptime(event.end.strftime(DATETIME_FORMAT), DATETIME_FORMAT)
            # add event's end and start to return_busy_list
            return_busy_list.append({"start": start, "end": end})
    # make filter to busy values that are in the interval where is user sleeping
    filtered_busy_list = busy_nonsense_filter(user=updated_user, busy_list=return_busy_list)
    # if user object have sleeping from in settings
    if updated_user.sleeping_from:
        # append to busy list time with start sleeping from to current day and 00:00:00 time to next day
        filtered_busy_list.append(
            # make value of dict with combination of current day and time from user settings
            {"start": datetime.datetime.combine(day, updated_user.sleeping_from),
             # make value of dict with combination of next day and 00:00:00 time
             "end": datetime.datetime.combine((day+datetime.timedelta(days=1)), datetime.time(00, 00))})
    # if user object have sleeping to in settings
    if updated_user.sleeping_to:
        # append in the first (0 index) position of busy list from 00:00:00 time to sleeping to of current day
        filtered_busy_list.insert(
            # make value of dict with combination of current day and 00:00:00 time
            0, {"start": datetime.datetime.combine(day, datetime.time(00, 00)),
                # make value of dict with combination of current dat and sleeping to time
                "end": datetime.datetime.combine(day, updated_user.sleeping_to)})
    # cut the null free intervals from busy list
    combined_busy_list = combine_null_break_intervals(busy_list=filtered_busy_list)
    # check if it need to be converted in free list
    if convert_free:
        # get free list from busy
        free_list = obtain_free_from_busy(user=updated_user, busy_list=combined_busy_list)
        # convert datetime values to string representation for future converting into JSON
        return stringify_busy_list(free_busy_list=free_list)
    # make busy_list
    else:
        # convert datetime values to string representation for future converting into JSON
        return stringify_busy_list(free_busy_list=combined_busy_list)


# make filter to busy values that are in the interval where is user sleeping
def busy_nonsense_filter(user, busy_list):
    filtered_busy_list = []
    for item in range(len(busy_list)):
        # filter if end of busy item less than datetime to which a user object sleeping to
        if busy_list[item]["end"] < datetime.datetime.combine(busy_list[item]["start"].date(), user.sleeping_to):
            pass
        # filter if end of busy item greater than datetime to which a user object sleeping from
        elif busy_list[item]["end"] > datetime.datetime.combine(busy_list[item]["end"], user.sleeping_from):
            pass
        # otherwise append item to filtered list
        else:
            filtered_busy_list.append({"start": busy_list[item]["start"], "end": busy_list[item]["end"]})
    return filtered_busy_list


# combine together intervals where end of current item the same as start of next item
def combine_null_break_intervals(busy_list):
    filtered_busy_list = []
    pause = None
    for item in range(len(busy_list)):
        # check if current item already combined and pass it
        if item == pause:
            continue
        # try to catch next item from busy list
        try:
            # check if end of current item equal the start of next item
            if busy_list[item]["end"] >= busy_list[item+1]["start"]:
                # combine it together and append to filtered list (start of current item and end of next item)
                filtered_busy_list.append({"start": busy_list[item]["start"], "end": busy_list[item + 1]["end"]})
                # make the variable to pass the next item in iteration
                pause = item + 1
            else:
                # otherwise append current common item (current start and current end)
                filtered_busy_list.append({"start": busy_list[item]["start"], "end": busy_list[item]["end"]})
        # haven't next item in the busy list
        except IndexError:
            # otherwise append current common item (current start and current end)
            filtered_busy_list.append({"start": busy_list[item]["start"], "end": busy_list[item]["end"]})
    return filtered_busy_list


# convert busy list to free list
def obtain_free_from_busy(user, busy_list):
    free_list = []
    # iteration through the length of busy list -1
    for item in range(len(busy_list)-1):
        # check if start datetime from next item of busy list is...
        # greater than (datetime of current item date and time when user is sleeping to)
        # and less than (the start datetime from current item of busy list)
        if datetime.datetime.combine(busy_list[item]["start"].date(), user.sleeping_to) \
                < busy_list[item+1]["start"] < busy_list[item]["end"]:
            pass
        # check if start datetime from next item of busy list is...
        # greater than (datetime of current item date and time when user is sleeping from)
        elif datetime.datetime.combine(busy_list[item]["start"].date(), user.sleeping_from) < busy_list[item+1]["start"]:
            pass
        # otherwise append dict with (end datetime of current item and start datetime of next item) to free list
        else:
            free_list.append({"start": busy_list[item]["end"], "end": busy_list[item+1]["start"]})
    return free_list


# convert python datetime into string representation
def stringify_busy_list(free_busy_list):
    # iteration through the free or busy list
    for item in free_busy_list:
        # get key:value from item
        for key, date_time in item.items():
            # convert item with current key to ISO string format with UTC timezone
            item[key] = date_time.strftime(DATETIME_FORMAT)
    return free_busy_list
