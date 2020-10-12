from django.http import JsonResponse
from googleapiclient.discovery import build
from rest_framework.response import Response

from contacts.models import UserGoogleContacts


def create_contacts_from_api(user, http=None):
    # build the API service to calendar v3 with authorized credentials
    '''
        To get the user's profile, use the following code:
     profile = people_service.people().get('people/me', personFields='names,emailAddresses')
        To get the person information for any Google Account, use the following code:
     profile = people_service.people().get('account_id', personFields='names,emailAddresses')

    '''

    service = build('people', 'v1', http=http)
    # generate scope for query to People API personFields
    # list_of_scopes = ['addresses', 'ageRanges', 'biographies', 'birthdays', 'braggingRights',
    #                   'coverPhotos', 'emailAddresses', 'events', 'genders', 'imClients',
    #                   'interests', 'locales', 'memberships', 'metadata', 'names',
    #                   'nicknames', 'occupations', 'organizations', 'phoneNumbers', 'photos',
    #                   'relations', 'relationshipInterests', 'relationshipStatuses', 'residences',
    #                   'skills', 'taglines', 'urls', 'userDefined']
    list_of_scopes = ['names', 'phoneNumbers', 'emailAddresses']
    person_fields_list = ','.join(list_of_scopes)
    # make query to Google people v1 API and execute() it to the dictionary
    #contacts_list = service.people().connections().list(
    #    resourceName='people/me',
    #    personFields=person_fields_list).execute()
    connections = service.people().connections().list(resourceName='people/me', personFields=person_fields_list).execute()
    #profile = people_service.people().get('people/me', personFields='names,emailAddresses')

    #profile = service.people().get('ivanteg@gmail.com', personFields='names,emailAddresses,phoneNumbers')
    # contacts_list = service.people().get(resourceName='people/me',
    #                                      personFields='names,phoneNumbers,emailAddresses').execute()
    current_user_contacts = UserGoogleContacts.objects.filter(user=user).values('contact_id')
    check_ids(user, contacts_list['connections'], current_user_contacts)
    #print(connections)
    # return contacts_list #['connections']
    return connections

def check_ids(user, items_dict, user_contacts):
    real_ids_list = []
    current_ids_list = []
    list_to_create = []
    list_to_update = []
    list_to_delete = []
    # iteration through the api response dict with scoped contacts
    for contact in items_dict:
        real_ids_list.append(contact['resourceName'])
    # iteration through user contacts and take contact_id
    for contact in user_contacts:
        current_ids_list.append(contact['contact_id'])
    # iteration through real_ids_list to make create or update
    for contact_id in real_ids_list:
        # check that contact_id inside current_id_list
        if contact_id in current_ids_list:
            list_to_update.append(contact_id)
        else:
            list_to_create.append(contact_id)
    # iteration through current_ids_list to make delete
    for contact_id in current_ids_list:
        # check that contact_id not inside real_ids_list
        if contact_id not in real_ids_list:
            list_to_delete.append(contact_id)
    return make_updates(user, items_dict, list_to_create, list_to_update, list_to_delete)


def make_updates(user, items_dict=None, list_to_create=None,
                 list_to_update=None, list_to_delete=None):
    if list_to_delete:
        delete_query = UserGoogleContacts.objects.filter(contact_id__in=list_to_delete)
        if delete_query.exists():
            delete_query.delete()
    if list_to_create:
        if len(list_to_create) == 1:
            for item in items_dict:
                if item['resourceName'] in list_to_create:
                    kwargs = create_contact_kwargs(item)
                    UserGoogleContacts.objects.create(user=user, **kwargs)
        else:
            bulk_create_list = []
            for item in items_dict:
                if item['resourceName'] in list_to_create:
                    kwargs = create_contact_kwargs(item)
                    bulk_create_list.append(UserGoogleContacts(user=user, **kwargs))
            UserGoogleContacts.objects.bulk_create(bulk_create_list)
    # TODO: optimize update queries to DB
    if list_to_update:
        for item in items_dict:
            if item['resourceName'] in list_to_update:
                kwargs = create_contact_kwargs(item, cut_id=True)
                UserGoogleContacts.objects.filter(user=user, contact_id=item['resourceName']).update(**kwargs)
    return None


def create_contact_kwargs(contact, cut_id=False):
    # list of values to cut from kwargs
    not_needed_keys = ['etag']
    # add renamed id (contact_id) to list
    if cut_id is True:
        not_needed_keys.append('contact_id')
    # dictionary of keys with old_name: renamed_name to use with UserContacts model
    renamed_keys = {
        'resourceName': 'contact_id',
        'names': {'givenName': 'first_name', 'familyName': 'last_name', 'displayName': 'display_name'},
        'phoneNumbers': {'canonicalForm': 'phone'},
        'emailAddresses': {'value': 'email'},
        'contact': 'contact_profile'
    }
    kwargs = {}
    for key, value in contact.items():
        # if the key from contact iteration located in dict < renamed_keys >
        if key in renamed_keys.keys():
            # if type of response value is a python list()
            if type(value) is list:
                # take the dict by key in dict < renamed_keys >
                ins_dict = renamed_keys[key]
                if len(value) > 1:
                    # iteration through the list < value[1] >
                    for item in value[1]:
                        # check if item inside the list same as key inside ins_dict.keys()
                        if item in ins_dict.keys():
                            # insert to dict of kwargs:
                                # KEY = value by ins_dict where key=item,
                                # VALUE = is value of current item inside list < value[1] >
                            kwargs[ins_dict[item]] = value[1][item]
                else:
                    for item in value[0]:
                        if item in ins_dict.keys():
                            kwargs[ins_dict[item]] = value[0][item]
            else:
                # use renamed key name for this value
                kwargs[renamed_keys[key]] = value
        # otherwise use default key name for this value
        else:
            kwargs[key] = value
    # add contact_profile
    kwargs[renamed_keys['contact']] = contact
    for key in not_needed_keys:
        if key in kwargs.keys():
            # cut key from kwargs
            kwargs.pop(key)
    # print(kwargs)
    return kwargs
