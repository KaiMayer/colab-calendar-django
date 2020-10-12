from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from googleapiclient.discovery import build
from django.core import serializers
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.renderers	import	JSONRenderer
from api.serializers_specific.serializers_calendars import  NLayersSerializer
from calendars.models import UserCalendars, UserCalendarLayer
# from api.utils.common import get_cred
# from accounts.models import User


def create_calendars_from_api(user, http=None):
    # build the API service to calendar v3 with authorized credentials
    service = build('calendar', 'v3', http=http)
    # make query to Google calendar v3 API and execute() it to the dictionary
    # Returns entries on the user's calendar list.
    calendar_list = service.calendarList().list().execute()

    current_user_calendars = UserCalendars.objects.filter(user=user).values('calendar_id')
    check_ids(user, calendar_list['items'], current_user_calendars)

    return calendar_list['items']


def check_ids(user, items_dict, user_calendars):
    real_ids_list = []
    current_ids_list = []
    list_to_create = []
    list_to_update = []
    list_to_delete = []
    # iteration through the api response dict with scoped calendars
    for calendar in items_dict:
        real_ids_list.append(calendar['id'])
    # iteration through user calendars and take calendar_id
    for calendar in user_calendars:
        current_ids_list.append(calendar['calendar_id'])
    # iteration through real_ids_list to make create or update
    for calendar_id in real_ids_list:
        # check that calendar_id inside current_id_list
        if calendar_id in current_ids_list:
            list_to_update.append(calendar_id)
        else:
            list_to_create.append(calendar_id)
    # iteration through current_ids_list to make delete
    for calendar_id in current_ids_list:
        # check that calendar_id not inside real_ids_list
        if calendar_id not in real_ids_list:
            list_to_delete.append(calendar_id)
    return make_updates(user, items_dict, list_to_create, list_to_update, list_to_delete)


def make_updates(user, items_dict=None, list_to_create=None,
                 list_to_update=None, list_to_delete=None):
    if list_to_delete:
        delete_query = UserCalendars.objects.filter(calendar_id__in=list_to_delete)
        if delete_query.exists():
            delete_query.delete()
    if list_to_create:
        if len(list_to_create) == 1:
            for item in items_dict:
                if item['id'] in list_to_create:
                    kwargs = create_calendar_kwargs(item)
                    UserCalendars.objects.create(user=user, **kwargs)
        else:
            bulk_create_list = []
            for item in items_dict:
                if item['id'] in list_to_create:
                    kwargs = create_calendar_kwargs(item)
                    bulk_create_list.append(UserCalendars(user=user, **kwargs))
            UserCalendars.objects.bulk_create(bulk_create_list)
    # TODO: optimize update queries to DB
    if list_to_update:
        for item in items_dict:
            if item['id'] in list_to_update:
                kwargs = create_calendar_kwargs(item, cut_id=True)
                UserCalendars.objects.filter(user=user, calendar_id=item['id']).update(**kwargs)
    return None


def update_layers(user, items_dict=None, list_to_create=None,
                 list_to_update=None, list_to_delete=None):
    '''
     update layers in table
    :param user: user for update
    :param items_dict: all layers from google
    :param list_to_create:
    :param list_to_update:
    :param list_to_delete:
    :return:
    '''
    if list_to_delete:
        delete_query = UserCalendarLayer.objects.filter(layer_id__in=list_to_delete)
        if delete_query.exists():
            delete_query.delete()
    if list_to_create:
        if len(list_to_create) == 1:
            for item in items_dict:
                if item['id'] in list_to_create:
                    kwargs = create_calendar_kwargs(item)
                    UserCalendarLayer.objects.create(user=user, **kwargs)
        else:
            bulk_create_list = []
            for item in items_dict:
                if item['id'] in list_to_create:
                    kwargs = create_calendar_kwargs(item)
                    bulk_create_list.append(UserCalendarLayer(user=user, **kwargs))
                    UserCalendarLayer.objects.bulk_create(bulk_create_list)
    # TODO: optimize update queries to DB
    if list_to_update:
        for item in items_dict:
            if item['id'] in list_to_update:
                kwargs = create_calendar_kwargs(item, cut_id=True)
                UserCalendarLayer.objects.filter(user=user, layer_id=item['id']).update(**kwargs)
    return None


def create_calendar_kwargs(calendar, cut_id=False):
    '''
     cut google layer (calendar) dictionary (reject not nededed data)
    :param calendar: layer data
    :param cut_id:  cut or no calendar_id
    :return:  new dictionary of layer data
    '''
    # list of values to cut from kwargs
    not_needed_keys = ['kind', 'etag', 'conferenceProperties', 'location', 'summaryOverride',
                       'hidden', 'deleted','defaultReminders','notificationSettings','accessRole']
    # add renamed id (calendar_id) to list
    if cut_id is True:
        not_needed_keys.append('calendar_id')
    # dictionary of keys with old_name: renamed_name to use with UserCalendars model
    renamed_keys = {
        'id': 'calendar_id', 'summary': 'calendar_title', 'description': 'calendar_description',
        'timeZone': 'time_zone', 'colorId': 'color_id', 'backgroundColor': 'color_background',
        'foregroundColor': 'color_foreground',
          }
    kwargs = {}
    for key, value in calendar.items():
        if key == 'primary':
            kwargs['primary'] = True
        else:
            kwargs['primary'] = False
        # if the key from calendar iteration located in renamed_keys
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

    kwargs['provider'] = 'google'
    # print(kwargs)
    return kwargs

def create_layer_kwargs(calendar, cut_id=False):
    '''
     cut google layer (calendar) dictionary (reject not nededed data)
    :param calendar: layer data
    :param cut_id:  cut or no calendar_id
    :return:  new dictionary of layer data
    '''
    # list of values to cut from kwargs
    not_needed_keys = ['kind', 'etag', 'conferenceProperties', 'location', 'summaryOverride',
                       'hidden', 'deleted', 'defaultReminders', 'notificationSettings']
    # add renamed id (calendar_id) to list
    if cut_id is True:
        not_needed_keys.append('calendar_id')
    # dictionary of keys with old_name: renamed_name to use with UserCalendars model
    renamed_keys = {
        'id': 'layer_id', 'summary': 'layer_title', 'description': 'layer_description',
        'timeZone': 'time_zone', 'colorId': 'color_id', 'backgroundColor': 'color_background',
        'foregroundColor': 'color_foreground', 'accessRole':'access_role',
    }
    kwargs = {}
    for key, value in calendar.items():
        # if the key from calendar iteration located in renamed_keys
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

def layer_kwargs_todb(calendar):
    '''
     cut google layer (calendar) dictionary (reject not nededed data)
    :param calendar: layer data
    :param cut_id:  cut or no calendar_id
    :return:  new dictionary of layer data
    '''
    # list of values to cut from kwargs
    not_needed_keys = ['kind', 'etag', 'conferenceProperties', 'location', 'summaryOverride',
                       'hidden', 'deleted', 'defaultReminders', 'notificationSettings']
    # add renamed id (calendar_id) to list
    # dictionary of keys with old_name: renamed_name to use with UserCalendars model
    renamed_keys = {
        'id': 'ids', 'summary': 'layer_title', 'description': 'layer_description',
        'timeZone': 'time_zone', 'colorId': 'color_id', 'backgroundColor': 'color_background',
        'foregroundColor': 'color_foreground', 'accessRole':'access_role',
    }
    kwargs = {}
    for key, value in calendar.items():
        # if the key from calendar iteration located in renamed_keys
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
    kwargs['provider'] = 'google'
    # print(kwargs)
    return kwargs

def layer_kwargs_fromdb(layer):
    '''
     cut google layer (calendar) dictionary (reject not nededed data)
    :param calendar: layer data
    :param cut_id:  cut or no calendar_id
    :return:  new dictionary of layer data
    '''
    # list of values to cut from kwargs
    not_needed_keys = ['kind', 'etag', 'conferenceProperties', 'location', 'summaryOverride',
                       'hidden', 'deleted', 'defaultReminders', 'notificationSettings']
    # add renamed id (calendar_id) to list
    # dictionary of keys with old_name: renamed_name to use with UserCalendars model
    renamed_keys = {
        'id': 'ids', 'summary': 'layer_title', 'description': 'layer_description',
        'timeZone': 'time_zone', 'colorId': 'color_id', 'backgroundColor': 'color_background',
        'foregroundColor': 'color_foreground', 'accessRole':'access_role',
    }
    kwargs = {}
    for key, value in layer.items():
        # if the key from calendar iteration located in renamed_keys
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
    kwargs['provider'] = 'google'
    # print(kwargs)
    return kwargs




def layer_kwargs (calendar, cut_id=False):
    '''
     cut google layer (calendar) dictionary (reject not nededed data)
    :param calendar: layer data
    :param cut_id:  cut or no calendar_id
    :return:  new dictionary of layer data
    '''
    # list of values to cut from kwargs
    not_needed_keys = ['kind', 'etag', 'conferenceProperties', 'location', 'summaryOverride',
                       'hidden', 'deleted', 'defaultReminders', 'notificationSettings']
    # add renamed id (calendar_id) to list
    if cut_id is True:
        not_needed_keys.append('calendar_id')
    # dictionary of keys with old_name: renamed_name to use with UserCalendars model
    renamed_keys = {
        'id': 'layer_id', 'description': 'layer_description',
        'timeZone': 'time_zone', 'colorId': 'color_id', 'backgroundColor': 'color_background',
        'foregroundColor': 'color_foreground', 'accessRole':'access_role',
    }
    kwargs = {}
    kwargs['is_active'] = True
    for key, value in calendar.items():
        if key=='primary':
            kwargs['primary'] = True
        else:
            kwargs['primary'] = False

        # if the key from calendar iteration located in renamed_keys
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



def add_new_calendars_from_api(user, http=None):
    # build the API service to calendar v3 with authorized credentials
    service = build('calendar', 'v3', http=http)
    # make query to Google calendar v3 API and execute() it to the dictionary
    # Returns entries on the user's calendar list.
    #calendars = service.calendarList().get(calendarId='primary').execute()
    calendars = service.calendarList().list().execute()
    #calendar =  service.calendars().(calendarId='primary').execute()

    # current_user_calendars = UserCalendars.objects.filter(user=user).values('calendar_id')
    # check_ids(user, calendar_list['items'], current_user_calendars)

    return calendars

def add_new_calendar_from_api(user, http=None):
    # build the API service to calendar v3 with authorized credentials
    service = build('calendar', 'v3', http=http)
    # make query to Google calendar v3 API and execute() it to the dictionary
    # Returns entries on the user's primary calendar
    calendar = service.calendarList().get(calendarId='primary').execute()
    kwargs = create_calendar_kwargs(calendar)
    # UserCalendar.objects.create_or_update(user=user, **kwargs)
    calendar = kwargs
    calendar['user'] = user.pk
    calendar['provider'] = 'google'
    calendar['email'] = user.email
    calendar['name'] = user.email123456

    return calendar




def add_new_calendar (user, calendar_id, calendar_title, provider, color_id, is_active = True):
    '''
     add new or update exiting calendar for user to db
    :param user: user id  - integer from accounts_user
    :param calendar_d - if =0 then new (add)? otherwise update for this id
    :return: new calendar in json
    '''
    calendar = {'calendar':{'user':user.username,
                'user_id':user.pk,
                'calendar_id':calendar_id,
                'calendar_title':calendar_title,
                'provider': provider,
                'color_id':color_id,
                'is_active': is_active},
                'error': None,
                'status':None}

    if calendar_id==0:
        n = UserCalendars.objects.create(user_id = user.pk,calendar_title=calendar_title,provider=provider,color_id = color_id, is_active = is_active)
        n.save()
        calendar['calendar']['calendar_id'] = n.pk
        calendar['status'] = 'Create new calendar in DB'
    else:
        co = UserCalendars.objects.filter(id=calendar_id)
        co.update(user_id=user.pk, calendar_title = calendar_title,  provider=provider,color_id=color_id, is_active=is_active)
        calendar['status'] = 'Update calendar in DB'

    return calendar


def new_layer (layer_id, calendar_id, name, provider, color_id,color_background,color_foreground, selected,time_zone, \
               access_role ='owner', is_active = True):
    '''
     add new or update exiting layer for user to db
    :param user: user id  - integer from accounts_user
    :param calendar_d - if =0 then new (add)? otherwise update for this id
    :return: new calendar in json
    '''
    layer = {'layer':{'id': layer_id,
                'calendar_id':calendar_id,
                'name':name,
                'provider': provider,
                'color_id':color_id,
                'color_background': color_background,
                'color_foreground': color_foreground,
                'selected': selected,
                'time_zone':time_zone,
                'access_role':access_role,
                'is_active': is_active},
                'error': None,
                'status':None }


    if layer_id==0:
        layer['status'] = 'Create new layer in DB'
        n = UserCalendarLayer.objects.create(calendar_id = calendar_id,layer_title=name,provider=provider,color_id = color_id, \
                                             color_background = color_background, color_foreground = color_foreground, \
                                             selected = selected, time_zone = time_zone, access_role= access_role, is_active = is_active)
        n.save()
        layer['layer']['id'] = n.pk
    else:
        layer['status'] = 'Update existing layer in DB'
        co = UserCalendarLayer.objects.filter(pk=layer_id)
        co.update(calendar_id = calendar_id,layer_title=name,provider=provider,color_id = color_id, \
                                             color_background = color_background, color_foreground = color_foreground, \
                                             selected = selected, time_zone = time_zone, access_role= access_role, is_active = is_active)
    return layer


def get_google_layers(user, http=None):
    '''
     synchronize user calendar in db - get from google actual layers
    :param user:
    :param http:
    :return:
    '''
    # build the API service to calendar v3 with authorized credentials
    service = build('calendar', 'v3', http=http)
    # make query to Google calendar v3 API and execute() it to the dictionary
    # Returns entries on the user's calendar list.
    layers = []
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            #if 'owner@qxf2.com' in calendar_list_entry['id']: -  here can get some filtr
            # layer = create_layer_kwargs(calendar_list_entry, cut_id=True)
            layer = layer_kwargs(calendar_list_entry, cut_id=True)
            layers.append(layer)
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break


    #current_user_layers = UserCalendarsLayers.objects.filter(user=user).values('calendar_id')
    #check_ids(user, calendar_list['items'], current_user_calendars)

    return layers

def google_layers_synchronize(user, calendar, http=None):
    '''
     synchronize user calendar in db - get from google actual layers
     calendar_id - integer unicum calendar id from db

    '''
    # build the API service to calendar v3 with authorized credentials
    service = build('calendar', 'v3', http=http)
    # make query to Google calendar v3 API and execute() it to the dictionary
    # Returns entries on the user's calendar list.
    layers = []
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            #if 'owner@qxf2.com' in calendar_list_entry['id']: -  here can get some filter
            # layer = create_layer_kwargs(calendar_list_entry, cut_id=True)
            layer = layer_kwargs_todb(calendar_list_entry)
            layers.append(layer)
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break


    # insert or update google layers in db
    # items=[]
    for layer in layers:
        layer['calendar_id'] = calendar.pk
        kwargs=layer
        # print(layer)
        # calendar = UserCalendarLayer.objects.update_or_create(calendar_id = calendar.pk,layer_title = layer['layer_id'])
        try:
            qs = UserCalendarLayer.objects.update_or_create(**kwargs)
            serializer = NLayersSerializer(qs, data=layer)
            print('Update layer')
        except ObjectDoesNotExist:
            #UserCalendarLayer.objects.create(**kwargs)
            print('Insert layer')

    layers = UserCalendarLayer.objects.filter(calendar_id = calendar.pk)
    serializer = NLayersSerializer(layers, many=True)
    return serializer.data


def layers_synchronize(user):
    '''
     synchronize user calendar in db - get from google actual layers
     all credentials from google must exists in db  - get caelndars and layers for  all user accounts
    '''
    result={}
    calendar_l=[]
    calendar_list= UserCalendars.objects.filter(user=user)
    for calendar in calendar_list:
        cserializer = NewCalendarSerializer(data=calendar)
        calendar_id = serializer.data['id']
        result['layers'] = layers
        c_item = serializer.data
        email = calendar.email
        http, res = get_cred(user, email)
        if http is not None:
            layers = google_layers_synchronize(user, calendar, http)
            c_item['layers'] = layers
        calendar_l.append(c_item)
    result = calendar_l

    return Response(result, status=status.HTTP_201_CREATED)



def google_layers_list(user, http=None):
    '''
     get all google layers list fro current user
     :param user:
    :param http:
    :return:
    '''
    # build the API service to calendar v3 with authorized credentials
    service = build('calendar', 'v3', http=http)
    # make query to Google calendar v3 API and execute() it to the dictionary
    # Returns entries on the user's calendar list.
    calendars = []
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            #if 'owner@qxf2.com' in calendar_list_entry['id']: -  here can get some filtr
            #layer = create_layer_kwargs(calendar_list_entry, cut_id=True)
            calendars.append(calendar_list)
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break

    for k in calendars["items"]:
        for c in k:
            if c == "id" or c == "summary" \
                    or c == "timeZone" or c == "backgroundColor" \
                    or c == "foregroundColor" or c == "accessRole" \
                    or c == "primary":
                calendar_id.append(k[c])
        page_token = calendar_list.get('nextPageToken')
    for i in calendar_id:
        calendar_list_entry = service.calendarList().get(calendarId=i).execute()
        calendar = service.calendars().get(calendarId=i).execute()


    return layers



def layers_updates(user, items_dict=None, list_to_create=None,
                 list_to_update=None, list_to_delete=None):
    '''
     MAYBE NOT NEED!  - update only one layer! from google not stored in db
     update layers get from google in db for user

    '''
    if list_to_delete:
        delete_query = UserCalendarLayer.objects.filter(layer_id__in=list_to_delete)
        if delete_query.exists():
            delete_query.delete()
    if list_to_create:
        if len(list_to_create) == 1:
            for item in items_dict:
                if item['id'] in list_to_create:
                    kwargs = create_calendar_kwargs(item)
                    UserCalendarLayer.objects.create(user=user, **kwargs)
        else:
            bulk_create_list = []
            for item in items_dict:
                if item['id'] in list_to_create:
                    kwargs = create_calendar_kwargs(item)
                    bulk_create_list.append(UserCalendarLayer(user=user, **kwargs))
                    UserCalendarLayer.objects.bulk_create(bulk_create_list)
    # TODO: optimize update queries to DB
    if list_to_update:
        for item in items_dict:
            if item['id'] in list_to_update:
                kwargs = create_calendar_kwargs(item, cut_id=True)
                UserCalendarLayer.objects.filter(user=user, calendar_id=item['id']).update(**kwargs)
    return None



def filter_layers(layer):
    '''
     filter only need key in layer
    :param layer:  layer (calendar from calendar list )
    :return:
    '''
    flayer={}
    klist= ["selected","id","summary","foregroundColor","backgroundColor","accessRole","etag","description","timeZone","colorId"]
    not_needed_keys = ['kind', 'etag', 'conferenceProperties', 'location', 'summaryOverride',
                       'hidden', 'deleted']
    renamed_keys = {
        'id': 'calendar_id', 'summary': 'layer_title', 'description': 'layer_description',
        'timeZone': 'time_zone', 'colorId': 'color_id', 'backgroundColor': 'color_background',
        'foregroundColor': 'color_foreground', 'accessRole': 'access_role',
        'defaultReminders': 'default_reminders', 'notificationSettings': 'notifications',
    }
    flayer = {}
    for key, value in layer:
        # if the key from calendar iteration located in renamed_keys
        if key in klist:
            if key in renamed_keys.keys():
                # use renamed key name for this value
                flayer[renamed_keys[key]] = value
            # otherwise use default key name for this value
        else:
            flayer[key] = value

    for key in not_needed_keys:
        if key in flayer.keys():
            # cut key from kwargs
            flayer.pop(key)

    return flayer

def add_new_layer (calendar_id, layer_title, provider, color_id, is_active = True):
    '''
     add new layer for calendar to db
    :param user: user id  - integer from accounts_user
    :return: new layer in json
    '''
    if provider == None:
        provider='timicate'
    layer = {'layer':{'calendar_id':calendar_id,
                        'layer_id':None,
                     'layer_title':layer_title,
                        'provider': provider,
                       'color_id' : color_id,
                       'is_active': is_active},
                 'error': None,
                 'status':None }
    # add new db record

    layer['status'] = 'Create new calendar in DB'
    UserCalendarLayer.objects.create(calendar_id = calendar_id,layer_title=layer_title,provider=provider,is_active = is_active,color_id=color_id)
    queryset = UserCalendarLayer.objects.filter(calendar_id = calendar_id, layer_title = layer_title)
    c_id = queryset.id
    layer['layer']['layer_id'] = c_id

    return layer

def update_layer (calendar_id,layer_id, name, color_id, is_active = True):
    '''
     add new layer for calendar to db
    :param user: user id  - integer from accounts_user
    :return: new layer in json
    '''
    layer = {'layer':{'calendar_id':calendar_id,
                'layer_id':layer_id,
                'name':name,
                'provider': provider,
                'color_id' : color_id,
                'is_active': is_active},
                 'error': None,
                 'status':None }
    # add new db record
    layer['status'] = 'Update layer '+name+' in DB'
    try:
        UserCalendarLayer.objects.update(calendar_id = calendar_id,name=name,provider=provider,is_active = is_active,color_id=color_id)
    except Exception as e:
        layer['error'] = 'Error: '+ str(e)

    return layer


def delete_layer (layer_id):
    '''
     add new layer for calendar to db
    :param user: user id  - integer from accounts_user
    :return: new layer in json
    '''
    result =    {'layer':{'calendar_id':None,
                'layer_id':layer_id,
                'name':None,
                'provider': None,
                'color_id' : None,
                'is_active': None},
                 'error': None,
                 'status':None }
    # add new db record
    qs = UserCalendarLayer.objects.get(id = layer_id)
    if not qs:
        result['error'] = 'Error: record (layer) not exists!'
        return result
    else:
        result['calendar_id'] =qs[0]['calendar_id']
        result['name'] = qs[0]['name']
        result['provider'] = qs[0]['provider']
        result['color_id'] = qs[0]['color_id']
        result['is_active'] = qs[0]['is_active']
        layer['status'] = 'Delete layer '+name+' from DB'
        try:
            qs.delete()
            result['status'] = 'Succesfully delete layer ' + name + ' from DB'
        except Exception as e:
            result['error'] = 'Error: '+ str(e)

    return result
