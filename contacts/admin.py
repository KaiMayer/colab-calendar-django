from django.contrib import admin

from contacts.models import UserGoogleContacts, UserContacts


@admin.register(UserGoogleContacts)
class UserGoogleContacts(admin.ModelAdmin):
    list_display = ('user', 'contact_id', 'first_name', 'last_name', 'display_name', 'email', 'phone', 'contact_profile')


@admin.register(UserContacts)
class UserContacts(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'phone', 'email', 'in_app_user')
