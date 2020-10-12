from django.urls import path, re_path, include
# from rest_auth.views import LogoutView, LoginView
from api.views import LoginView, LogoutView

from api.views import UserListApiView, UserInfo, UserDevicesApiView, FacebookConfirm, GoogleConfirm, \
    ObtainGoogleColorsAPIView, FacebookLogin, GoogleLogin
from api.views_specific.views_calendars import CalendarListApiView, CalendarSyncApiView,\
     LayersSyncApiView,CalendarEditView,LayerEditView, CalendarAddApiView, CalendarActiveView, LayersSyncronizeView ,CalendarAuthorize
from api.views_specific.views_contacts import GoogleContactsListApiView, GoogleContactsSyncApiView, \
    UserContactsListCreateApiView, UserContactRetrieveUpdateDeleteApiView
from api.views_specific.views_events import EventsAPIView, CalendarEventListApiView, CalendarEventDetailApiView, \
    CalendarEventSyncApiView, TemicateEventAPIView, UserPollsListAPIView, UserPollRetrieveUpdateAPIView, \
    TemicateEventRetrieveUpdateDestroyAPIView, EventTimeSlotRetrieveUpdateDestroyAPIView, \
    EventTimeSlotListCreateAPIView, EventTimeSlotVoteAPIView,TimeSlotCreateAPIView,TemicateEventsListAPIView
from api.views_specific.views_freebusy import UserFreeBusySyncApiView, UserFreeListAPIView
from api.views_specific.views_events import CalendarEventFromGoogle,TeamicateEventAddApiView,EventsByFilterAPIView
from . import views

urlpatterns = [
    path('', views.UserListApiView.as_view()),
    # re_path(r'^rest-auth/', include('rest_auth.urls')),
    re_path(r'^user/fb/login/$', FacebookLogin.as_view(), name='fb_login'),
    re_path(r'^user/google/login/$', GoogleLogin.as_view(), name='google_login'),
    re_path(r'^accounts/', include('allauth.urls')),
]

# Social login links
urlpatterns += [
    # re_path(r'^user/google/login/$', GoogleLoginApiView.as_view(), name='google_login'),
    re_path(r'^user/google/login/v2/', GoogleConfirm.as_view(), name='google_login2'),
    # re_path(r'^user/fb/login/$', FacebookLoginApiView.as_view(), name='facebook_login'),
    # re_path(r'^user/fb/login/v2', FacebookCheck.as_view(), name='facebook_login2'),
    re_path(r'^user/fb/login/v2/', FacebookConfirm.as_view(), name='facebook_login2'),
    # re_path(r'^user/login/$', LoginView.as_view(), name='login'),
    # re_path(r'^user/logout/$', LogoutView.as_view(), name='logout'),
    re_path(r'^user/login/$', LoginView.as_view(), name='login'),
    re_path(r'^user/logout/$', LogoutView.as_view(), name='logout'),
    re_path(r'^user/registration/', include('rest_auth.registration.urls')),
    re_path(r'^user/user-list/$', UserListApiView.as_view(), name='user_list'),
    re_path(r'^user/device/$', UserDevicesApiView.as_view(), name='user_device'),
    re_path(r'^user/$', UserInfo.as_view(), name='user'),
]

# API views to get or update Database from Google elements (calendars/events/contacts/accesses)
urlpatterns += [
    re_path(r'^user/calendars/synchronize', CalendarSyncApiView.as_view()), # get goole calendars
    re_path(r'^user/calendars/list', CalendarListApiView.as_view()), # get google calendars from db
    # re_path(r'^user/calendars/new', CalendarAddView.as_view()), # not needd - add new in
    re_path(r'^user/calendar$', CalendarAddApiView.as_view()), # get google calendars - for compatibility with app
    # re_path(r'^user/calendar/(?P<calendar_id>.+)$', CalendarDetailApiView.as_view()),
    re_path(r'^user/calendar/(?P<calendar_id>.+)/active$', CalendarActiveView.as_view()),
    # re_path(r'^user/autorize$', CalendarAuthorize.as_view()), # for test google authorize only

    # re_path(r'^user/calendars/(?P<calendar_id>.+)$', CalendarEditView.as_view()),     # add or edit teamicate calendar
    re_path(r'^user/calendar/(?P<calendar_id>.+)$', CalendarEditView.as_view()),  # add or edit teamicate calendar

    # re_path(r'^user/calendars/layers/(?P<calendar_id>.+)$', LayersDetailView.as_view()),
    # re_path(r'^user/calendars/layers/', LayerAddView.as_view()),
    # re_path(r'^user/calendars/layers/', LayerEditView.as_view()),
    re_path(r'^user/calendars/layer/(?P<layer_id>.+)$', LayerEditView.as_view()),     # add, edit, delete layer
    # re_path(r'^user/calendars/layers/synchronize', LayersSyncApiView.as_view()),      # get google calendars layers (insted x)
    re_path(r'^user/calendars/layers/synchronize', LayersSyncronizeView.as_view()),      # get google calendars layers (insted x)


    re_path(r'^user/contacts/', UserContactsListCreateApiView.as_view()),
    re_path(r'^user/contact/(?P<contact_id>.+)$', UserContactRetrieveUpdateDeleteApiView.as_view()),
    # exchange
    #re_path(r'^user/google-contacts/synchronize', GoogleContactsListApiView.as_view()),
    #re_path(r'^user/google-contacts/list', GoogleContactsSyncApiView.as_view()),
    re_path(r'^user/google-contacts/synchronize', GoogleContactsSyncApiView.as_view()),
    re_path(r'^user/google-contacts/list', GoogleContactsListApiView.as_view()),

    re_path(r'^user/events/synchronize', CalendarEventSyncApiView.as_view()),
    # get only teamicate events for current user
    re_path(r'^user/events/tlist', TemicateEventsListAPIView.as_view()),
    # TO DO - get list only timicate events
    # TO DO - get list combine timicate events + google events
    # get google events from db - not need ! - maybe combened list
    re_path(r'^user/events/list', CalendarEventListApiView.as_view()),

    re_path(r'^user/events/glist', CalendarEventFromGoogle.as_view()),
    re_path(r'^user/events/add', TeamicateEventAddApiView.as_view()),
    re_path(r'^user/events/(?P<event_id>.+)$', CalendarEventDetailApiView.as_view()),
    # /events/external/ events from google (and maybe from other)
    re_path(r'^events/external', CalendarEventFromGoogle.as_view(), name="external_event"),
    # get both event from google and teamicate by given period
    re_path(r'^events/byDate', EventsByFilterAPIView.as_view(), name="event_bydate"),
    # TO DO

    re_path(r'^google/colors', ObtainGoogleColorsAPIView.as_view(), name="google_colors"),
    re_path(r'^user/freebusy/synchronize', UserFreeBusySyncApiView.as_view(), name="user_freebusy"),


    re_path(r'^event/(?P<id>\d+)$', TemicateEventRetrieveUpdateDestroyAPIView.as_view(),
            name="temicate_event_detail"),
    re_path(r'^event/$', TemicateEventAPIView.as_view(), name="temicate_event"),

    # TO DO - /events/timeslots/ all timeslots in system ?
    re_path(r'^events/timeslots/', TimeSlotCreateAPIView.as_view()),

    re_path(r'^event/(?P<event_id>\d+)/timeslots/$', EventTimeSlotListCreateAPIView.as_view()),
    re_path(r'^event/(?P<event_id>\d+)/timeslot/(?P<id>\d+)$',
            EventTimeSlotRetrieveUpdateDestroyAPIView.as_view()),
    re_path(r'^event/(?P<event_id>\d+)/timeslot/(?P<id>\d+)/vote/$',
            EventTimeSlotVoteAPIView.as_view()),

    re_path(r'^user/free-list', UserFreeListAPIView.as_view(), name="user_free_list"),
    re_path(r'^user/polls/list', UserPollsListAPIView.as_view(), name="user_polls_list"),
    re_path(r'^user/poll/(?P<pk>\d+)$', UserPollRetrieveUpdateAPIView.as_view(), name="user_polls_list"),
]

# API views to update Google elements (calendars/events/contacts/accesses)
urlpatterns += [
    re_path(r'^user/event', EventsAPIView.as_view()),
]
