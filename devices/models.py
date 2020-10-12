from django.db import models
from accounts.models import User


class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_type = models.CharField(max_length=100)
    token = models.CharField(max_length=400)
    arn = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'device'
        verbose_name_plural = 'devices'

    def __str__(self):
        return '% %'.format(str(self.user), self.device_type)
