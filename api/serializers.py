from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

from calendars.models import UserCalendars
from devices.models import Device
from contacts.models import UserGoogleContacts

User = get_user_model()


class UserSignUpSerializer(serializers.ModelSerializer):
    _error_messages = {
        'required': 'Required field cannot be left blank.',
        'password': 'Password do not much.',
        'email': 'This Email address is already in use.',
        'username': 'This username address is already in use.'
    }
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError(self._error_messages['email'])
        return value

    # def validate_username(self, value):
    #     if User.objects.filter(username__iexact=value).exists():
    #         raise ValidationError(self._error_messages['username'])
    #     return value

    def validate(self, attrs):
        password = attrs['password']
        password2 = attrs['password2']

        if password != password2:
            raise ValidationError(self._error_messages['password'])

        return attrs

    def save(self, request, *args, **kwargs):
        self.validated_data.pop('password2')
        self._extra_data = {
            "password": self.validated_data.pop('password'),
        }
        return super(UserSignUpSerializer, self).save(**kwargs)

    def create(self, validated_data):
        instance = User.objects.create(**validated_data)
        instance.set_password(self._extra_data['password'])
        instance.save()
        return instance

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'phone',
            'sleeping_from',
            'sleeping_to',
            'password',
            'password2',
            'registered'
        )


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password', 'groups', 'user_permissions')


class UserDetailSerializer(serializers.ModelSerializer):
    error_messages = {
        'required': 'This field is required.',
    }
    image_thumbnail_url = serializers.ImageField(source='get_thumbnail', read_only=True)
    password = serializers.CharField(required=False, write_only=True)
    password2 = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise ValidationError('You must type the same password each time.')
        return attrs

    def save(self, **kwargs):
        self._extra_data = {
            "password": self.validated_data.pop('password2', None),
        }
        return super(UserDetailSerializer, self).save(**kwargs)

    def create(self, validated_data):
        if self._extra_data['password']:
            instance = User.objects.create(**validated_data)
            instance.set_password(self._extra_data['password'])
            instance.save()
            return instance
        super(UserDetailSerializer, self).create(validated_data)

    class Meta:
        model = User
        exclude = (
            'user_permissions', 'groups', 'last_login', 'is_active',
            'is_superuser', 'is_staff'
        )
        read_only_fields = (
            'date_joined',
        )


class TokenSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)

    class Meta:
        model = Token
        fields = ('key', 'user')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'phone',
            'sleeping_from',
            'sleeping_to',
            'registered'
        )
        model = User


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        write_only = ('password',)
