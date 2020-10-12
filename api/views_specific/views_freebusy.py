from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers_specific.serializers_freebusy import UserFreeBusySerializer, UserFreeListSerializer
from api.utils.common import make_credentials
from api.utils.utils_freebusy import get_user_freebusy_list
from events.models import UserFreeBusy


class UserFreeBusySyncApiView(generics.ListAPIView):
    serializer_class = UserFreeBusySerializer
    permission_classes = (IsAuthenticated,)
    queryset = UserFreeBusy.objects.all()

    def get(self, request, *args, **kwargs):
        current_user = self.request.auth.user
        items = make_credentials(request=self.request, user=current_user, freebusy=True)
        if "error" in items:
            return Response(items, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(items, status=status.HTTP_200_OK)


class UserFreeListAPIView(generics.GenericAPIView):
    serializer_class = UserFreeListSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        free_dict = {}
        if serializer.validated_data["sync"]:
            from api.utils.common import make_credentials
            make_credentials(request=request, user=self.request.auth.user, freebusy=True)
        for day in serializer.validated_data["list_of_days"]:
            free_dict[str(day)] = get_user_freebusy_list(
                request=self.request, user=self.request.auth.user,
                day=day, sync_before=False, convert_free=True
            )
        return Response(free_dict, status=status.HTTP_201_CREATED)