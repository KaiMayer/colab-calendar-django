from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserCredentials


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'phone', 'sleeping_from', 'sleeping_to')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Sleeping time', {'fields': ('sleeping_from', 'sleeping_to')}),
    )


@admin.register(UserCredentials)
class UserCredentials(admin.ModelAdmin):
    list_display = ('user', 'json_credentials')
