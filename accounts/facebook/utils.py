import json
from json import JSONDecodeError

import httplib2
from django.utils.crypto import get_random_string
from django.utils.http import urlencode

from outbizzed.settings.base import FACEBOOK_APP_ID, FACEBOOK_SCOPES, \
    FACEBOOK_REDIRECT_URL, FACEBOOK_RESPONSE_TYPE, FACEBOOK_APP_SECRET


def generate_obtain_code_link():
    link_part = 'https://www.facebook.com/v3.0/dialog/oauth?'
    client_part = 'client_id=' + FACEBOOK_APP_ID
    redirect_part = '&redirect_uri=' + FACEBOOK_REDIRECT_URL
    auth_type = '&auth_type=' + 'rerequest'
    scope_part = '&scope=' + ','.join(FACEBOOK_SCOPES)
    state_part = '&state=' + get_random_string(length=20)
    response_type = '&response_type=' + FACEBOOK_RESPONSE_TYPE
    link = link_part+client_part+redirect_part+auth_type+scope_part+state_part+response_type
    # print(link))
    return link


def get_access_token_from_code(code):
    link_part = 'https://graph.facebook.com/v3.0/oauth/access_token?'
    client_id = 'client_id=' + FACEBOOK_APP_ID
    redirect_part = '&redirect_uri=' + FACEBOOK_REDIRECT_URL
    client_secret = '&client_secret=' + FACEBOOK_APP_SECRET
    code = '&code=' + code
    link = link_part+client_id+redirect_part+client_secret+code
    # print(link)
    response = httplib2.Http().request(link)
    # print(response)
    info = json.loads(response[1])
    # print(info)
    if 'access_token' in info:
        return {"access_token": info['access_token']}
    else:
        return {"error": info['error']}
    # return link


def get_facebook_info(access_token):
    scopes = ['id', 'email', 'first_name', 'last_name', 'name']
    link_part = 'https://graph.facebook.com/v3.0/me?fields='
    scope_part = '%2C'.join(scopes)
    access_part = '&access_token=' + access_token
    link = link_part+scope_part+access_part
    # print(link)
    response = httplib2.Http().request(link)
    # print(response)
    try:
        user = json.loads(response[1])
        return {"message": user}
    except JSONDecodeError:
        return {"error": "access_token has been used or incorrect"}


# def generate_obtain_code_link():
#     url = 'https://www.facebook.com/v3.0/dialog/oauth?'
#     query_params = {
#         'client_id': FACEBOOK_APP_ID,
#         'redirect_uri': FACEBOOK_REDIRECT_URL,
#         'auth_type': 'rerequest',
#         'scope': ','.join(FACEBOOK_SCOPES),
#         'state': get_random_string(length=20),
#         'response_type': FACEBOOK_RESPONSE_TYPE
#     }
#     return ''.join([url, urlencode(query_params)])
#
#
# def get_access_token_from_code(code):
#     url = 'https://graph.facebook.com/v3.0/oauth/access_token?'
#     query_params = {
#         'client_id': FACEBOOK_APP_ID,
#         'redirect_uri': FACEBOOK_REDIRECT_URL,
#         'client_secret': FACEBOOK_APP_SECRET,
#         'code': code
#     }
#     response = httplib2.Http().request("".join([url, urlencode(query_params)]))
#     info = json.loads(response[1])
#     if 'access_token' in info:
#         return {"access_token": info['access_token']}
#     else:
#         return {"error": info['error']}
#
#
# def get_facebook_info(access_token):
#     url = 'https://graph.facebook.com/v3.0/me?fields='
#     query_params = {
#         'access_token': access_token,
#         'fields': '%2C'.join(FACEBOOK_SCOPES)
#     }
#     response = httplib2.Http().request("".join([url, urlencode(query_params)]))
#     try:
#         user = json.loads(response[1])
#         return {"message": user}
#     except:
#         return {"error": "access_token has been used or incorrect"}
