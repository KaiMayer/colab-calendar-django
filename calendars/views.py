import httplib2
from oauth2client import client
from oauth2client.client import OAuth2WebServerFlow, AccessTokenRefreshError
from googleapiclient.discovery import build
# from apiclient.discovery import build

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.views.generic import View

from outbizzed.settings.base import GOOGLE_CLIENT_SECRET, GOOGLE_SCOPES
from accounts.models import UserCredentials
from calendars.models import UserCalendars

from braces.views import LoginRequiredMixin


class CompleteView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        flow = OAuth2WebServerFlow(
            client_id=GOOGLE_CLIENT_SECRET["CLIENT_ID"],
            client_secret=GOOGLE_CLIENT_SECRET["CLIENT_SECRET"],
            scope=GOOGLE_SCOPES["CALENDAR_PEOPLE"],
            redirect_uri=GOOGLE_CLIENT_SECRET["REDIRECT_URIS"]
        )
        auth_uri = flow.step1_get_authorize_url()

        try:
            current_user_creds = UserCredentials.objects.get(user=self.request.user)
            credential_object = client.Credentials.new_from_json(json_data=current_user_creds.json_credentials)
            # print(credential_object)
            if credential_object:
                try:
                    http = credential_object.authorize(httplib2.Http())
                # TODO: try to handle exception for expired token that cannot refresh
                except:
                    return JsonResponse({"message": "Authorize failed"})
        except ObjectDoesNotExist:
            auth_code = self.request.GET.get('code')
            # print(auth_code)
            if auth_code:
                # TODO: make exceptions for random code or already used code.
                credentials = flow.step2_exchange(code=auth_code, http=None)
                json_credentials = credentials.to_json()

                UserCredentials.objects.create(
                    user=self.request.user,
                    json_credentials=json_credentials
                )
                http = credentials.authorize(httplib2.Http())
            else:
                return HttpResponseRedirect(auth_uri)

        return self.create_calendars_from_api(http=http)

    def create_calendars_from_api(self, http=None):
        # build the API service to calendar v3 with authorized credentials
        service = build('calendar', 'v3', http=http)
        # make query to Google calendar v3 API and execute() it to the dictionary
        calendar_list = service.calendarList().list().execute()

        current_user_calendars = UserCalendars.objects.filter(user=self.request.user).values('calendar_id')

        self.check_ids(calendar_list['items'], current_user_calendars)

        return TemplateResponse(self.request, 'base.html', {"calendars": calendar_list['items']})

    def create_calendar_kwargs(self, calendar, cut_id=False):
        # list of values to cut from kwargs
        not_needed_keys = ['kind', 'etag', 'conferenceProperties']
        # add renamed id (calendar_id) to list
        if cut_id is True:
            not_needed_keys.append('calendar_id')
        # dictionary of keys with old_name: renamed_name to use with UserCalendars model
        renamed_keys = {
            'id': 'calendar_id', 'summary': 'calendar_title', 'description': 'calendar_description',
            'timeZone': 'time_zone', 'colorId': 'color_id', 'backgroundColor': 'color_background',
            'foregroundColor': 'color_foreground', 'accessRole': 'access_role',
            'defaultReminders': 'default_reminders', 'notificationSettings': 'notifications',
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
            # cut key from kwargs
            kwargs.pop(key)
        # print(kwargs)
        return kwargs

    def check_ids(self, items_dict, user_calendars):
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
        return self.make_updates(items_dict, list_to_create, list_to_update, list_to_delete)

    def make_updates(self, items_dict=None, list_to_create=None,
                     list_to_update=None, list_to_delete=None):
        if list_to_delete:
            delete_query = UserCalendars.objects.filter(calendar_id__in=list_to_delete)
            if delete_query.exists():
                delete_query.delete()
        if list_to_create:
            if len(list_to_create) == 1:
                for item in items_dict:
                    if item['id'] in list_to_create:
                        kwargs = self.create_calendar_kwargs(item)
                        UserCalendars.objects.create(user=self.request.user, **kwargs)
            else:
                bulk_create_list = []
                for item in items_dict:
                    if item['id'] in list_to_create:
                        kwargs = self.create_calendar_kwargs(item)
                        bulk_create_list.append(UserCalendars(user=self.request.user, **kwargs))
                UserCalendars.objects.bulk_create(bulk_create_list)
        # TODO: optimize update queries to DB
        if list_to_update:
            # all_users_calendars = UserCalendars.objects.filter(user=self.request.user)
            for item in items_dict:
                if item['id'] in list_to_update:
                    kwargs = self.create_calendar_kwargs(item, cut_id=True)
                    # all_users_calendars.filter(calendar_id=item['id']).update(**kwargs)
                    UserCalendars.objects.filter(user=self.request.user, calendar_id=item['id']).update(**kwargs)
        return None
