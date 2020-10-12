from django.conf import settings
from django.contrib.auth import (
    logout as django_logout
)
from rest_auth.app_settings import create_token
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView

from accounts.facebook.utils import generate_obtain_code_link, get_facebook_info, get_access_token_from_code
from accounts.google.utils import create_google_link_from_settings, build_service_from_flow_and_code, \
    make_google_api_query
from accounts.models import User
from api.utils.common import make_credentials
from devices.models import Device

from .serializers import UserSerializer, UserDeviceSerializer

from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from rest_auth.registration.views import SocialLoginView
from rest_auth.views import LoginView as RestAuthLoginView
from rest_auth.views import LogoutView as RestAuthLogoutView


class UserListApiView(generics.ListAPIView):
    """
    List of registered users
    """
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = UserSerializer
    paginate_by = 20


class UserInfo(generics.RetrieveUpdateDestroyAPIView):
    """
    User information by id
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_queryset(self):
        # queryset = User.objects.filter(pk=self.kwargs['user_id'])
        queryset = User.objects.filter(pk=self.request.auth.user.pk)
        return queryset

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset)
        self.check_object_permissions(self.request, obj)
        return obj

    def put(self, request, *args, **kwargs):

        if 'registered' not in kwargs.keys():
            kwargs['registered'] = "True"
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        kwargs['registered'] = 'True'
        return self.partial_update(request, *args, **kwargs)


class UserDevicesApiView(generics.ListAPIView):
    serializer_class = UserDeviceSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Device.objects.all()

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        return queryset


class FacebookConfirm(GenericAPIView):
    http_method_names = ['get']

    # http_method_names = ['get', 'post']
    # serializer_class = UserSignUpSerializer

    def get(self, request, *args, **kwargs):
        try:
            code = self.request.query_params.get("code")
            access_token = get_access_token_from_code(code)
            if "error" in access_token:
                return Response(access_token, status=status.HTTP_403_FORBIDDEN)
            user_data = get_facebook_info(access_token['access_token'])
            if "message" in user_data:
                kwargs = {}
                user_dict = user_data['message']
                if user_dict['id']:
                    kwargs['id'] = user_dict['id']
                if user_dict['first_name']:
                    kwargs['first_name'] = user_dict['first_name']
                if user_dict['last_name']:
                    kwargs['last_name'] = user_dict['last_name']
                if user_dict['email']:
                    kwargs['email'] = user_dict['email']
                return Response(kwargs, status=status.HTTP_200_OK)
                # return Response(user_data, status=status.HTTP_200_OK)
            else:
                return Response(user_data, status=status.HTTP_403_FORBIDDEN)
        except TypeError:
            # error = self.request.query_params.get("error")
            # return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)
            link = generate_obtain_code_link()
            # print(link)
            return Response({"facebook access url": link}, status=status.HTTP_200_OK)

    # def post(self, request, *args, **kwargs):
    #     if self.request.query_params.get("password"):
    #         kwargs['password'] = self.request.query_params.get("password")
    #     if self.request.query_params.get("password2"):
    #         kwargs['password2'] = self.request.query_params.get("password2")
    #     if self.request.query_params.get("username"):
    #         kwargs['username'] = self.request.query_params.get("username")
    #     if kwargs:
    #         serializer = UserSignUpSerializer(data=kwargs)
    #         if serializer.is_valid():
    #             serializer.save(self, request, *args, **kwargs)
    #             return Response({"message": "created"}, status=status.HTTP_201_CREATED)
    #         else:
    #             return Response(data={"serializer": serializer.data, "errors": serializer.errors},
    #                             status=status.HTTP_400_BAD_REQUEST)
    #     else:
    #         return Response({"error": "something"}, status=status.HTTP_400_BAD_REQUEST)


class GoogleConfirm(GenericAPIView):
    http_method_names = ['get']

    def get(self, request, code=None, *args, **kwargs):
        code = self.request.query_params.get("code")
        if code is None:
            link = create_google_link_from_settings()
            # print(link)
            return Response({"google access url": link}, status=status.HTTP_200_OK)
        else:
            people_service = build_service_from_flow_and_code(flow=None, code=code)
            response = make_google_api_query(service=people_service)
            if "error" in response:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            else:
                kwargs = {"id": ((((response["names"])[0])["metadata"])["source"])["id"],
                          "first_name": ((response["names"])[0])["givenName"],
                          "last_name": ((response["names"])[0])["familyName"],
                          "email": ((response["emailAddresses"])[0])["value"]}
                return Response({"message": kwargs}, status=status.HTTP_200_OK)


class ObtainGoogleColorsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        service = make_credentials(request=request, user=current_user, to_google=True)
        return self.make_api_call(service)

    def make_api_call(self, service):
        try:
            colors = service.colors().get().execute()
            [colors.pop(key) for key in ["kind", "updated"]]
            # print(colors)
            return Response(colors, status.HTTP_200_OK)
        except:
            return Response({"error": "can't obtain google colors"}, status.HTTP_400_BAD_REQUEST)


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


class LoginView(RestAuthLoginView):
    def login(self):
        self.user = self.serializer.validated_data['user']

        # if getattr(settings, 'REST_USE_JWT', False):
        #     self.token = jwt_encode(self.user)
        # else:
        #     self.token = create_token(self.token_model, self.user,
        #                               self.serializer)
        self.token = create_token(self.token_model, self.user, self.serializer)

        if getattr(settings, 'REST_SESSION_LOGIN', True):
            self.process_login()


class LogoutView(RestAuthLogoutView):
    def logout(self, request):
        # try:
        #     request.user.auth_token.delete()
        # except (AttributeError, ObjectDoesNotExist):
        #     pass

        django_logout(request)

        return Response({"detail": "Successfully logged out."},
                        status=status.HTTP_200_OK)
