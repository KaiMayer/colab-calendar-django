from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from api.serializers_specific.serializers_contacts import UserContactSerializer, UserGoogleContactSerializer, UserContactRetrieveUpdateSerializer
from api.utils.common import make_credentials
from contacts.models import UserGoogleContacts, UserContacts


class GoogleContactsListApiView(generics.ListAPIView):
    serializer_class = UserGoogleContactSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = UserGoogleContacts.objects.filter(user=self.request.auth.user)
        return queryset


class GoogleContactsSyncApiView(generics.ListAPIView):
    serializer_class = UserGoogleContactSerializer
    permission_classes = (IsAuthenticated,)
    # queryset = UserGoogleContacts.objects.all()

    def get(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        items = make_credentials(request=self.request, user=current_user, contacts=True)
        if "error" in items:
            return Response(items, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(items, status=status.HTTP_200_OK)


class UserContactsListCreateApiView(generics.ListCreateAPIView):
    serializer_class = UserContactSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = UserContacts.objects.filter(user=self.request.auth.user)
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        if isinstance(data, list):
            serializer = self.get_serializer(data=request.data, many=True)
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        try:
            if serializer.validated_data["phone"]:
                try:
                    in_app_user = User.objects.get(phone=serializer.validated_data["phone"])
                    serializer.save(user=self.request.auth.user, in_app_user=True, email=in_app_user.email)
                except User.DoesNotExist:
                    serializer.save(user=self.request.auth.user)
        except:
            try:
                if serializer.validated_data["email"]:
                    try:
                        in_app_user = User.objects.get(email=serializer.validated_data["email"])
                        serializer.save(user=self.request.auth.user, in_app_user=True, phone=in_app_user.phone)
                    except User.DoesNotExist:
                        serializer.save(user=self.request.auth.user)
            except:
                serializer.save(user=self.request.auth.user)


class UserContactRetrieveUpdateDeleteApiView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserContactRetrieveUpdateSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "id"
    lookup_url_kwarg = "contact_id"

    def get_queryset(self):
        queryset = UserContacts.objects.filter(user=self.request.auth.user)
        return queryset

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        try:
            if serializer.validated_data["phone"]:
                try:
                    in_app_user = User.objects.get(phone=serializer.validated_data["phone"])
                    serializer.save(in_app_user=True, email=in_app_user.email)
                except User.DoesNotExist:
                    serializer.save()
        except:
            try:
                if serializer.validated_data["email"]:
                    try:
                        in_app_user = User.objects.get(email=serializer.validated_data["email"])
                        serializer.save(in_app_user=True, phone=in_app_user.phone)
                    except User.DoesNotExist:
                        serializer.save()
            except:
                serializer.save()
