from rest_framework import permissions


class IsEventCreator(permissions.BasePermission):
    message = "You have no permissions for edit this TemicateEvent"

    def has_object_permission(self, request, view, obj):
        if request.auth.user == obj.creator:
            return True
        else:
            return False


class IsUserCanModify(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.users_can_modify:
            if request.auth.user.id in [user.id for user in obj.participants.all()]:
                return True
            else:
                return False
        else:
            return False


class IsEventCreatorOrUserCanModifyEvent(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.auth.user == obj.creator:
            return True
        elif obj.users_can_modify:
            if request.auth.user.id in [user.id for user in obj.participants.all()]:
                return True
        else:
            return False


class IsEventCreatorOrUserCanInvite(permissions.BasePermission):
    message = "You can't invite people for this TemicateEvent"

    def has_object_permission(self, request, view, obj):
        if request.auth.user == obj.creator:
            return True
        elif obj.users_can_invite:
            if request.auth.user.id in [user.id for user in obj.participants.all()]:
                return True
        else:
            return False


class IsEventCreatorOrUserCanModifyTimeSlot(permissions.BasePermission):
    message = "You have no permissions for edit this TimeSlot"

    def has_object_permission(self, request, view, obj):
        if request.auth.user == obj.event.creator:
            return True
        elif obj.event.users_can_modify:
            if request.auth.user.id in [user.id for user in obj.event.participants.all()]:
                return True
        else:
            return False


class IsEventCreatorTimeSlot(permissions.BasePermission):
    message = "You have no permissions for edit this TemicateEvent"

    def has_object_permission(self, request, view, obj):
        if request.auth.user == obj.event.creator:
            return True
        else:
            return False


class UserPollPermissionOwner(permissions.BasePermission):
    message = "You haven't access for this TemicatePollUser"

    def has_object_permission(self, request, view, obj):
        if request.auth.user == obj.event_user:
            return True
        return False


class IsEventCreatorOrUserCanInviteOrModify(permissions.BasePermission):
    modify_fields_list = [
        'event_title', 'event_description', 'event_activity', 'polls', 'free', 'start', 'end',
        'status', 'location', 'users_can_modify', 'users_can_invite']

    def has_object_permission(self, request, view, obj):

        if request.auth.user == obj.creator:
            return True

        elif obj.users_can_invite and obj.users_can_modify:
            if ("users_can_modify" or "users_can_invite") in request.data.keys():
                self.message = "The 'users_can_modify' and 'users_can_invite' settings can change only creator"
                return False

        elif obj.users_can_invite and not obj.users_can_modify:
            if ("add_attendees" or "del_attendees") in request.data.keys():
                value_field_list = self.check_fields(request)
                if value_field_list[0]:
                    return True
                else:
                    self.message = "You have no permissions for edit this '{}' field".format(value_field_list[1])
                    return False

        elif not obj.users_can_invite and obj.users_can_modify:
            if ("add_attendees" or "del_attendees") in request.data.keys():
                self.message = "You can't invite people but can modify event"
                return False
            else:
                if ("users_can_modify" or "users_can_invite") in request.data.keys():
                    self.message = "The 'users_can_modify' and 'users_can_invite' settings can change only creator"
                    return False
                else:
                    return True
        else:
            self.message = "You have no permissions for edit this TemicateEvent"
            return False

    def check_fields(self, request):
        for field in self.modify_fields_list:
            if field in request.data.keys():
                return [False, field]
        return True
