from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from contacts.models import UserGoogleContacts, UserContacts


class UserGoogleContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGoogleContacts
        fields = '__all__'
        ordering = ('id',)


class UserContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserContacts
        fields = ('id', 'first_name', 'last_name', 'phone', 'email', 'in_app_user')
        ordering = ('id',)
        read_only_fields = ('id', 'in_app_user',)

    def validate(self, data):
        try:
            phone = data.get('phone')
        except:
            phone = None
        try:
            email = data.get('email')
        except:
            email = None
        if not phone and not email:
            raise ValidationError('Please provide phone or email for contact')
        return data


class UserContactRetrieveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserContacts
        fields = ('id', 'first_name', 'last_name', 'phone', 'email', 'in_app_user')
        ordering = ('id',)
        read_only_fields = ('id', 'in_app_user',)
