from rest_framework import serializers

from events.models import UserFreeBusy


class UserFreeBusySerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    class Meta:
        model = UserFreeBusy
        fields = '__all__'
        ordering = ('id',)


class UserFreeListSerializer(serializers.Serializer):
    sync = serializers.BooleanField(default=False)
    list_of_days = serializers.ListField(child=serializers.DateField())