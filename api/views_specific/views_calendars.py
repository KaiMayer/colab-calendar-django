import json
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers_specific.serializers_calendars import CalendarSerializer, CalendarCutSerializer,LayersSerializer,\
    NewCalendarSerializer,NLayersSerializer
from api.utils.common import make_credentials,make_cred, make_cred_code
from api.utils.utils_calendars import add_new_calendars_from_api, add_new_calendar,get_google_layers,add_new_layer, add_new_calendar_from_api, google_layers_synchronize
from calendars.models import UserCalendars,UserCalendarLayer
from accounts.models import  EmailAddress
#from rest_framework.renderers import JSONRenderer
#from rest_framework.parsers import JSONParser


class CalendarAuthorize(generics.ListAPIView):
    serializer_class = CalendarSerializer
    def post (self, request, *args, **kwargs):
        '''
         get list all calendars with layers
        '''

        if request.method == 'POST':
            current_user = self.request.auth.user
            data = self.request.data
            auth_code = data['access_data']['auth_code']
            email = data['email']
            result = {}
            new_calendar={}
            # http , res  = make_cred(request=self.request, user=current_user,email)
            print('Get credentianal for Aut_code', auth_code, 'Email:', email)
            http, res = make_cred_code(auth_code, current_user,email)

        return Response(res, status=status.HTTP_200_OK)



class CalendarListApiView(generics.ListAPIView):
    # serializer_class = CalendarSerializer
    serializer_class = CalendarCutSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = UserCalendars.objects.filter(user=self.request.auth.user)
        return queryset


class CalendarSyncApiView(generics.ListAPIView):
    serializer_class = CalendarSerializer
    # serializer_class = CalendarCutSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        return queryset

    def get(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        items = make_credentials(request=self.request, user=current_user, calendars=True)
        if "error" in items:
            return Response(items, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(items, status=status.HTTP_200_OK)

# class CalendarAddApiView(generics.ListAPIView):
#     #serializer_class = CalendarSerializer
#     serializer_class = CalendarCutSerializer
#     permission_classes = (IsAuthenticated,)
#
#     def post(self, request, *args, **kwargs):
#         current_user = self.request.auth.user
#         http, res = make_cred(request=self.request, user=current_user)
#         if http is not None:
#             print('Get primary calendar google')
#             calendar = add_new_calendar_from_api(current_user, http)
#
#         if not calendar:
#             return Response(calendar, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response(calendar, status=status.HTTP_200_OK)

class LayersSyncApiView(generics.ListAPIView):
    # synchronize all layers for user - get from google into db and return combine list
    # serializer_class = CalendarSeriaalizer
    # UserCalendarLayer
    serializer_class = NLayersSerializer
    permission_classes = (IsAuthenticated,)

    # def get_queryset(self):
    #     queryset = self.queryset.filter(user=self.request.user)
    #     # print(self.request.auth.user)
    #     # print(self.request.user)
    #     return queryset

    def get(self, request, *args, **kwargs):
        layers_list={'timicate_layers':[],
                     'google_layers':[]}
        current_user = self.request.auth.user.pk
        # get first from db
        query = [' calendar_id in (SELECT id FROM calendars_usercalendars where user_id= %s)']
        params = [self.request.auth.user.pk]
        print('Get layers from db for user ',current_user)
        queryset = UserCalendarLayer.objects.extra(where=query, params=params)
        # print(queryset)
        layers_list['timicate_layers'] = queryset
        # select *all calendars for user where provider='google'
        # for ech calendar get credentials if exist and synchronize layers


        http, res = make_cred(request=self.request, user=current_user)
        if http is not None:
            print('Get layers from google')
            items = get_google_layers(current_user, http)
            layers_list['google_layers'] = items

        # items = make_credentials(request=self.request, user=current_user, calendars=True)
        if "error" in items:
            #layers_list['google_layers'] = items
            return Response(layers_list, status=status.HTTP_400_BAD_REQUEST)
        else:
            #layers_list['google_layers'] = items
            return Response(layers_list, status=status.HTTP_200_OK)


class CalendarDetailApiView(generics.RetrieveAPIView):
    # serializer_class = CalendarSerializer
    serializer_class = CalendarCutSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "calendar_id"

    def get_queryset(self):
        queryset = UserCalendars.objects.filter(calendar_id=self.kwargs["calendar_id"])
        return queryset



class CalendarAddApiView(generics.ListAPIView):
    # serializer_class = CalendarSerializer
    serializer_class = CalendarCutSerializer
    permission_classes = (IsAuthenticated,)

    def get (self, request, *args, **kwargs):
        '''
         get list all calendars with layers
        '''
        if request.method == 'GET':
            result={}
            calendars_list = []
            # layers_list = []
            current_user = self.request.auth.user
            print('Get all calendars from db for user ', current_user)
            calendars = UserCalendars.objects.filter(user = self.request.auth.user)
            for calendar in calendars:
                oneres={}
                cserialiser = NewCalendarSerializer(calendar)
                # calendars_list.append(cserialiser.data)
                layers = UserCalendarLayer.objects.filter(calendar_id = calendar.pk)
                lserialiser = NLayersSerializer(layers,many=True)
                oneres=cserialiser.data
                oneres['layers'] = lserialiser.data
                calendars_list.append(oneres)
            result = calendars_list

        return Response(result, status=status.HTTP_200_OK)



    def post (self, request, *args, **kwargs):
        if request.method == 'POST':
            current_user = self.request.auth.user
            data =self.request.data
            auth_code = data['access_data']['auth_code']
            email = data['email']
            result={}
            # print('Get credentianal for Aut_code',auth_code, 'Email:', email)
            http, res = make_cred_code(auth_code,  self.request.auth.user, email)
            if http is not None:
                print(' Get primary calendar from google')
                new_calendar = add_new_calendar_from_api(current_user, http)
                # new_calendar['primary'] = True
                # print(new_calendar)
                # TO DO  - if email <> user.email and google aitorisation success - add to account_emailaddress
                if email != self.request.auth.user.email:
                    try:
                        eaddress = EmailAddress.objects.get(email = email, user_id= current_user)
                    except EmailAddress.DoesNotExist:
                        EmailAddress.objects.create(email=email,user_id= current_user,verified= True)
                        # EmailAdress.Create

                try:
                    calendar = UserCalendars.objects.get(user=self.request.user, calendar_id=new_calendar['calendar_id'])
                    serializer = NewCalendarSerializer(calendar, data=new_calendar)
                    print('Edit calendar')
                except  UserCalendars.DoesNotExist:
                    serializer = NewCalendarSerializer(data=new_calendar)
                    print('New calandar insert')
                if serializer.is_valid():
                    serializer.save()
                    calendar_id = serializer.data['id']
                    result=serializer.data
                    result ['email'] = self.request.auth.user.email
                    result['layers'] =[]
                    result['name'] = data['name']
                    # get google layers
                    calendar = UserCalendars.objects.get(user=self.request.user,
                                                         calendar_id=new_calendar['calendar_id'])
                    layers = google_layers_synchronize(current_user, calendar, http)
                    result['layers']= layers

                    return Response(result, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(res, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class CalendarTestApiView(generics.ListAPIView):
    # serializer_class = CalendarSerializer
    serializer_class = CalendarCutSerializer
    permission_classes = (IsAuthenticated,)

    def get (self, request, *args, **kwargs):
        '''
         get list all calendars with layers
        '''
        if request.method == 'GET':
            result={}
            calendars_list = []
            # layers_list = []
            current_user = self.request.auth.user
            print('Get all calendars from db for user ', current_user)
            calendars = UserCalendars.objects.filter(user = self.request.auth.user)
            for calendar in calendars:
                oneres={}
                cserialiser = NewCalendarSerializer(calendar)
                # calendars_list.append(cserialiser.data)
                layers = UserCalendarLayer.objects.filter(calendar_id = calendar.pk)
                lserialiser = NLayersSerializer(layers,many=True)
                oneres=cserialiser.data
                oneres['layers'] = lserialiser.data
                calendars_list.append(oneres)
            result = calendars_list

        return Response(result, status=status.HTTP_200_OK)



    def post (self, request, *args, **kwargs):
        if request.method == 'POST':
            current_user = self.request.auth.user
            data =self.request.data
            auth_code = data['access_data']['auth_code']
            email = data['email']
            result={}
            #http , res  = make_cred(request=self.request, user=current_user,email)
            print('Get credentianal for Aut_code',auth_code, 'Email:', email)
            http, res = make_cred_code(auth_code, current_user,email)

            if http is not None:
                print('Get primary calendar from google')
                new_calendar = add_new_calendar_from_api(current_user, http)
                # new_calendar['primary'] = True
                print(new_calendar)
                try:
                    calendar = UserCalendars.objects.get(user=self.request.user, calendar_id=new_calendar['calendar_id'])
                    serializer = NewCalendarSerializer(calendar, data=new_calendar)
                    print('Edit calendar')
                except  UserCalendars.DoesNotExist:
                    serializer = NewCalendarSerializer(data=new_calendar)
                    print('New calandar insert')
                if serializer.is_valid():
                    serializer.save()
                    calendar_id = serializer.data['id']
                    result=serializer.data
                    result ['email'] = self.request.auth.user.email
                    result['layers'] =[]
                    result['name'] = data['name']
                    # get google layers
                    calendar = UserCalendars.objects.get(user=self.request.user,
                                                         calendar_id=new_calendar['calendar_id'])
                    layers = google_layers_synchronize(current_user, calendar, http)
                    # rename key for app compability
                    #for layer in layers:
                    #   layer['layer_id'] = layer.pop('id')
                    #  # layer['layer_id'] = layer['id']
                    result['layers']= layers

                    return Response(result, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(res, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)



class CalendarAddView(generics.ListAPIView):
    # serializer_class = CalendarSerializer
    serializer_class = CalendarCutSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        user_id=self.request.auth.user.pk
        if request.method == 'POST':
            json_data = self.request.data  #json.loads(request.body.decode('utf8'))  # request.raw_post_data w/ Django < 1.4
            try:
                calendar_title = json_data["calendar_title"] or self.request.auth.user.email
                provider = json_data["provider"] or 'teamicate'
                color_id = json_data["color_id"] or 17
                is_active = json_data["is_active"] or "True"
                calendar_id= json_data["calendar_id"] or 0

            except KeyError:
                return Response({'error': 'Malformed data!'}, status=status.HTTP_400_BAD_REQUEST)

        # calendar = UserCalendars.objects.objects.update_or_create(calendar_id=self.kwargs["calendar_id"])
        # add to db create new default calenda for user
        new_calendar = add_new_calendar(current_user, calendar_id, calendar_title, provider, color_id, is_active)
        # get layers from google
        layers = None

        http,res  = make_cred(request=self.request, user=current_user)
        if http is not None:
            print('Get calendars from google')
            # new_calendar = add_new_calendars_from_api(current_user, http)
            # layers = add_new_calendars_from_api(current_user, http)
            layers = get_google_layers(current_user, http)
        # new_calendar = add_new_calendar(current_user, name, provider, is_active, http=None)
        if layers:
            new_calendar['google_layers'] = layers
        if not new_calendar:
            return Response({'error':'somthing wrang'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(new_calendar, status=status.HTTP_200_OK)


# class CalendarEditView(generics.ListAPIView):
#     # serializer_class = CalendarSerializer
#     serializer_class = NewCalendarSerializer
#     permission_classes = (IsAuthenticated,)
#
#
#     def get(self, request, *args, **kwargs):
#         # request.auth.user - object User (model)
#         current_user = self.request.auth.user
#         #print('Current user = ',self.request.auth.user.username)
#         # calendar_id = self.request.query_params.get('id', 0)
#         calendar_id = self.kwargs['calendar_id']
#         calendar = {'calendar': {'user': self.request.auth.user.username,
#                                  'user_id': self.request.auth.user.pk,
#                                  'calendar_id': calendar_id,
#                                  'calendar_title': None,
#                                  'provider': None,
#                                  'color_id': None,
#                                  'is_active': None},
#                     'error': None,
#                     'status': None}
#         #print('ID =',calendar_id)
#         if request.method == 'GET':
#             if calendar_id!=0:
#                co = UserCalendars.objects.filter(pk=calendar_id)
#                if co:
#                     calendar['calendar']['user_id'] =  co[0].user.id
#                     calendar['calendar']['calendar_id'] = co[0].id
#                     calendar['calendar']['calendar_title'] = co[0].calendar_title
#                     calendar['calendar']['provider'] = co[0].provider
#                     calendar['calendar']['color_id'] = co[0].color_id
#                     calendar['calendar']['is_active'] = co[0].is_active
#                     return Response(calendar, status=status.HTTP_200_OK)
#                else:
#                    calendar['error'] = 'Calendar '+calendar_id+ ' do not exists!'
#                    return Response({'error':'Calendar do not exist!'}, status=400)
#                    #HttpResponseServerError("Calendar dos not exist!")
#             else:
#                return Response({'error': 'Calendar dos not exist! Use POST method to add new calendar!'}, status=400)
#
#
#     def post(self, request, *args, **kwargs):
#         current_user = self.request.auth.user
#         calendar_id = self.kwargs['calendar_id']
#         # print('Request data:', str(self.request.data))
#         if request.method == 'POST':
#             json_data = self.request.data # json.loads(request.body.decode('utf8'))  # request.raw_post_data w/ Django < 1.4
#             try:
#                 calendar_id = json_data["calendar_id"] or 0
#                 calendar_title = json_data["calendar_title"]
#                 provider = json_data["provider"]
#                 color_id= json_data["color_id"]
#                 is_active = json_data["is_active"]
#             except KeyError:
#                  return Response({'error': 'Malformed data! Not all data passed!'}, status=400)
#             #HttpResponse("Got json data")
#             #print('Current user ',current_user)
#             new_calendar = add_new_calendar(current_user, calendar_id, calendar_title, provider, color_id, is_active, ) # add new calendar
#             return Response(new_calendar, status=status.HTTP_200_OK)
#
#     def delete (self, request, *args, **kwargs):
#         if request.method == 'DELETE':
#             calendar_id = self.kwargs['calendar_id']
#             co = UserCalendars.objects.filter(id=calendar_id)
#             try:
#                co.delete()
#                return Response({'status': 'deleted'}, status=status.HTTP_200_OK)
#             except Exception as e:
#                return Response({'error': str(e)}, status=404)


class CalendarActiveView(generics.ListAPIView):
    serializer_class = NewCalendarSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        calendar_id = self.kwargs['calendar_id']
        # active = self.kwargs['is_active']
        # print('Request data:', str(self.request.data))
        if request.method == 'POST':
            calendar = UserCalendars.objects.get(pk=calendar_id)
            # calendar.is_active = active
            json_data = self.request.data # json.loads(request.body.decode('utf8'))  # request.raw_post_data w/ Django < 1.4
            serializer = NewCalendarSerializer(calendar,data=self.request.data, partial = True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=205)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=HTTP_405_METHOD_NOT_ALLOWED)



class CalendarEditView(generics.ListAPIView):
    '''
         for insert new -put calendar_id = 0
        '''
    # serializer_class = CalendarSerializer
    serializer_class = NewCalendarSerializer
    permission_classes = (IsAuthenticated,)
    # queryset = UserCalendars.objects.filter(pk=calendar_id)

    def get_queryset(self, *args, **kwargs):
        current_user = self.request.auth.user
        calendar_id = self.kwargs['calendar_id']
        queryset = UserCalendars.objects.filter(pk=calendar_id)
        return queryset


    def post(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        calendar_id = self.kwargs['calendar_id'] or 0
        # print('Request data:', str(self.request.data))
        if request.method == 'POST':
            json_data = self.request.data # json.loads(request.body.decode('utf8'))  # request.raw_post_data w/ Django < 1.4
            serializer = NewCalendarSerializer(data=self.request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        calendar_id = self.kwargs['calendar_id']
        # print('Request data:', str(self.request.data))
        if request.method == 'PUT':
            calendar = UserCalendars.objects.get(pk=calendar_id)
            json_data = self.request.data # json.loads(request.body.decode('utf8'))  # request.raw_post_data w/ Django < 1.4
            serializer = NewCalendarSerializer(calendar,data=self.request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=205)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete (self, request, *args, **kwargs):
        if request.method == 'DELETE':
            calendar_id = self.kwargs['calendar_id']
            calendar =  UserCalendars.objects.filter(pk=calendar_id)
            try:
               calendar.delete()
               # return Response({'status': 'deleted'}, status=status.HTTP_200_OK)
               return Response({'status': 'deleted'}, status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
               return Response({'error': str(e)}, status=404)


class LayerEditView(generics.ListAPIView):
    '''
     for insert new - put layer_id=0
    '''
    # serializer_class = CalendarSerializer
    serializer_class = NLayersSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        current_user = self.request.auth.user
        layer_id = self.kwargs['layer_id']
        queryset = UserCalendarLayer.objects.filter(pk=layer_id)
        return queryset


    def post(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        # calendar_id = self.kwargs['calendar_id']
        layer_id = self.kwargs['layer_id'] or 0
        if request.method == 'POST':
            serializer = NLayersSerializer(data=self.request.data)
            print(str(serializer))
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        layer_id = self.kwargs['layer_id']
        if request.method == 'PUT':
            layer = UserCalendarLayer.objects.get(pk=layer_id)
            serializer = NLayersSerializer(layer,data=self.request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=205)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete (self, request, *args, **kwargs):
        if request.method == 'DELETE':
            layer_id = self.kwargs['layer_id']
            layer =  UserCalendarLayer.objects.filter(pk=layer_id)
            try:
               layer.delete()
               return Response({'status': 'deleted'}, status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
               return Response({'error': str(e)}, status=404)



class LayerAddView(generics.ListAPIView):

    # serializer_class = CalendarSerializer
    serializer_class = NLayersSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = UserCalendarLayer.objects.filter(layer_id=self.kwargs["layer_id"])
        return queryset

    def post(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        new_layer = None
        if request.method == 'POST':
            json_data = json.loads(request.body.decode('utf8'))  # request.raw_post_data w/ Django < 1.4
            #print('Json data:',json_data)
            # parse json to validate
            try:
                calendar_id = json_data["calendar_id"]
                layer_title = json_data["layer_title"]
                color_id = json_data["color_id"]
                is_active = json_data["is_active"]
                provider = json_data["provider"] or 'timicate'
                new_layer = add_new_layer(calendar_id, layer_title, provider, color_id, is_active = True)
            except KeyError:
                HttpResponseServerError("Malformed data!")


        if not new_layer:
            return Response({'error':'somthing wrang'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(new_layer, status=status.HTTP_200_OK)

class LayersListApiView(generics.ListAPIView):
        # serializer_class = CalendarSerializer
        serializer_class = NLayersSerializer
        permission_classes = (IsAuthenticated,)

        def get_queryset(self):
            '''
                get all layers fro db where calendar_id
            :return:
            '''
            user_id = self.request.auth.user.pk
            queryset = UserCalendarLayer.objects.filter(calendar = self.request.auth.user.pk)
            return queryset


class LayersSyncronizeView(generics.ListAPIView):
    # serializer_class = CalendarSerializer
    # serializer_class = CalendarCutSerializer
    permission_classes = (IsAuthenticated,)


    def post (self, request, *args, **kwargs):
        if request.method == 'POST':
            current_user = self.request.auth.user
            result = {}
            calendar_l = []
            calendar_list = UserCalendars.objects.filter(user=self.request.auth.user)
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


