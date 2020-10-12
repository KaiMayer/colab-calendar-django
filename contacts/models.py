from django.contrib.postgres.fields import JSONField
from django.db import models

from accounts.models import User


class UserGoogleContacts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    display_name = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(max_length=50, null=True, blank=True)
    contact_id = models.CharField("Contact ID", max_length=255, unique=True, null=True)
    contact_profile = JSONField("Contact profile", blank=True, null=True)

    class Meta:
        verbose_name = "User Google contact"
        verbose_name_plural = "User Google contacts"
        ordering = ('id',)

    def __str__(self):
        return self.display_name


class UserContacts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    in_app_user = models.BooleanField(default=False, blank=True)

    class Meta:
        verbose_name = "User contact"
        verbose_name_plural = "User contacts"
        ordering = ("id",)

    def __str__(self):
        return "{0} {1}".format(self.first_name, self.last_name)
