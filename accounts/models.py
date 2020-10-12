import datetime

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    username = models.CharField(max_length=80)
    phone = models.CharField(max_length=50, unique=True, blank=True, default = None)
    email = models.EmailField(max_length=100, unique=True, db_index=True)
    password = models.CharField(max_length=128)
    created_date = models.DateTimeField(default=timezone.now, blank=True)
    joined_date = models.DateTimeField(null=True, blank=True)
    time_zone = models.CharField(max_length=10)
    declined_events = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    sleeping_from = models.TimeField(null=True, blank=True, default=datetime.time(hour=22, minute=00, second=00))
    sleeping_to = models.TimeField(null=True, blank=True, default=datetime.time(hour=7, minute=00, second=00))
    registered = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

class EmailAddress(models.Model):
    user_id = models.ManyToOneRel(User, to='user_id',field_name='id',on_delete=models.CASCADE)
    email = models.EmailField(max_length=100, unique=True, db_index=True)
    primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User email adresses"
        verbose_name_plural = "User email adresses"


class UserCredentials(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    json_credentials = JSONField(null=True, blank=True)
    provider = models.CharField(max_length=100,default='google', null=True, blank=True)
    # email = models.ForeignKey(EmailAddress, on_delete = models.CASCADE)
    email = models.EmailField(max_length=100, unique=True, db_index=True)

    class Meta:
        verbose_name = "User credential"
        verbose_name_plural = "User credentials"
