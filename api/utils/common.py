import httplib2
from googleapiclient.discovery import build
from oauth2client import client
from oauth2client.client import OAuth2WebServerFlow, HttpAccessTokenRefreshError

from django.core.exceptions import ObjectDoesNotExist

from api.utils.utils_calendars import create_calendars_from_api
from api.utils.utils_contacts import create_contacts_from_api
from api.utils.utils_events import create_events_from_api
from api.utils.utils_freebusy import create_freebusy_from_api
# on settings.dev ???
from outbizzed.settings.base import GOOGLE_CLIENT_SECRET, GOOGLE_SCOPES
from accounts.models import UserCredentials
from datetime import datetime

def date_from_android(atime):
    millis = int(atime) / 1000
    truetime=datetime.fromtimestamp(millis)
    return truetime


def create_flow_from_settings():
    flow = OAuth2WebServerFlow(
        client_id=GOOGLE_CLIENT_SECRET["CLIENT_ID"],
        client_secret=GOOGLE_CLIENT_SECRET["CLIENT_SECRET"],
        scope=GOOGLE_SCOPES["CALENDAR_PEOPLE"],
        redirect_uri=GOOGLE_CLIENT_SECRET["REDIRECT_URIS"],
        access_type="offline",
        approval_prompt="force",
    )
    return flow

def make_cred (request, user, email, flow=None):
    out = {'credentials': False,
              'auth_uri':None,
                'status':None,
                 'error':None}

    http = None
    if flow is None:
        flow = create_flow_from_settings()
    auth_uri = flow.step1_get_authorize_url() # step1 - here we get NEW code !!!
    out['auth_uri']= auth_uri
    # print(auth_uri)
    if 'error' in auth_uri:
        err = auth_uri.split('?')[1]
        print('Error in first step authorization: '+err)
        out['error'] = err
    try:
        current_user_creds = UserCredentials.objects.get(user=user)
        credential_object = client.Credentials.new_from_json(json_data=current_user_creds.json_credentials)
        out['status'] = 'Get credentials from db'
        if not credential_object.access_token_expired: # token exist and not expired
            try:
                http = credential_object.authorize(httplib2.Http())
                out['status'] = 'Authorization on google success'
                print('Authorization on google success')
                out['credentials'] = True
            # TODO: try to handle exception for expired token that cannot refresh
            except Exception as e:
                err = str(e)
                out['status'] = 'Authorize on google failed'
                print('authorize failed', err)
                out['error'] = err

        else:  # token exist and expired
            try:
                credential_object.refresh(httplib2.Http())
                out['status'] = 'Refresh credentials on google success'
                print('Refresh credentials on google success')
                http = credential_object.authorize(httplib2.Http())
                #  update ceredential if change in db
                json_credentials = credential_object.to_json()
                UserCredentials.objects.update_or_create(
                    user=user,
                    defaults={"json_credentials": json_credentials}
                )
                #return http, out
            except HttpAccessTokenRefreshError:
                auth_code = request.query_params.get("code")
                out['status'] = 'Refresh failed - get from code'
               # print('Refresh failed - get from code')
                http, res = credentials_from_code(auth_code, user, auth_uri, flow)
                out['error'] = res['error']
                out['status'] = res['status']
                print(res['error'], res['status'])
               # return http, out

    # credention not exist in db
    except ObjectDoesNotExist:
        auth_code = request.query_params.get("code")
        # if not auth_code:

        out['status'] = 'Credentials no exist in db - get new from code'
        #print('Get credentials from code: ',auth_code)
        http, res = credentials_from_code(auth_code, flow, user,  auth_uri)
        out['error'] = res['error']
        out['status'] = res['status']
        print(res['error'],res['status'])

    return http, out

def make_cred_code (code, user, email, flow=None):
    '''
      full process obtaining google credentials for accounts (by email)
      work with multiple google accounts of user
    '''
    out = {'credentials': False,
              'auth_uri':None,
                'status':None,
                 'error':None}

    print('Get code from ',code, email)
    http = None
    if flow is None:
        flow = create_flow_from_settings()
    auth_uri = flow.step1_get_authorize_url() # step1 - here we get NEW code !!!
    out['auth_uri']= auth_uri
    # print(auth_uri)
    if 'error' in auth_uri:
        err = auth_uri.split('?')[1]
        print('Error in first step authorization: '+err)
        out['error'] = err
    try:
        current_user_creds = UserCredentials.objects.get(user= user, email= email)
        credential_object = client.Credentials.new_from_json(json_data=current_user_creds.json_credentials)
        out['status'] = 'Get credentials from db'
        if not credential_object.access_token_expired: # token exist and not expired
            try:
                http = credential_object.authorize(httplib2.Http())
                out['status'] = 'Authorization on google success'
                print('Authorization on google success')
                out['credentials'] = True
            # TODO: try to handle exception for expired token that cannot refresh
            except Exception as e:
                err = str(e)
                out['status'] = 'Authorize on google failed'
                print('authorize failed', err)
                out['error'] = err

        else:  # token exist and expired
            try:
                credential_object.refresh(httplib2.Http())
                out['status'] = 'Refresh credentials on google success'
                print('Refresh credentials on google success')
                http = credential_object.authorize(httplib2.Http())
                #  update ceredential if change in db
                json_credentials = credential_object.to_json()
                UserCredentials.objects.update_or_create(
                    user=user,email=email,
                    defaults={"json_credentials": json_credentials}
                )
                #return http, out
            except HttpAccessTokenRefreshError:
                auth_code = code # request.query_params.get("code")
                out['status'] = 'Refresh failed - get from code'
               # print('Refresh failed - get from code')
                http, res = cred_from_code(auth_code, user, email, auth_uri, flow)
                out['error'] = res['error']
                out['status'] = res['status']
                print(res['error'], res['status'])
               # return http, out

    # credention not exist in db
    except ObjectDoesNotExist:
        auth_code = code
        # if not auth_code:
        out['status'] = 'Credentials no exist in db - get new from code'
        print('Get credentials from code: ',auth_code,email,auth_uri)
        http, res = cred_from_code(auth_code, user, email, auth_uri, flow)
        out['error'] = res['error']
        out['status'] = res['status']
        print(res['error'],res['status'])

    return http, out


def make_credentials(request, user, flow=None, http=None,
                     calendars=False, events=False, accesses=False,
                     contacts=False, freebusy=False, to_google=False, *args, **kwargs):
    out = {'credentials':None,
              'auth_uri':None,
                'status':None,
                'error':None}

    if flow is None:
        flow = create_flow_from_settings()
    auth_uri = flow.step1_get_authorize_url() # step1 - here we get NEW code !!!
    out['auth_uri']= auth_uri
    # print(auth_uri)
    if 'error' in auth_uri:
        err = auth_uri.split('?')[1]
        print('Error in first step authorization: '+err)
        out['error'] = err
    try:
        current_user_creds = UserCredentials.objects.get(user=user)
        credential_object = client.Credentials.new_from_json(json_data=current_user_creds.json_credentials)
        out['status'] = 'from db'
        # print(credential_object)
        if not credential_object.access_token_expired: # token exist and not expired
            try:
                http = credential_object.authorize(httplib2.Http())
                out['status'] = 'authorization success'
                print('authorization success')
                out['http'] = str(http)
            # TODO: try to handle exception for expired token that cannot refresh
            except Exception as e:
                err = str(e)
                out['status'] = 'authorize failed'
                print('authorize failed', err)
                out['error'] = err
                return out
                # return {"error": err}
        else:  # token exist and expired
            try:
                credential_object.refresh(httplib2.Http())
                out['status'] = 'refresh success'
                print('refresh success')
                http = credential_object.authorize(httplib2.Http())
                out['http'] = str(http)
                #  update ceredential if change in db
                json_credentials = credential_object.to_json()
                UserCredentials.objects.update_or_create(
                    user=user,
                    defaults={"json_credentials": json_credentials}
                )
            except HttpAccessTokenRefreshError:
                auth_code = request.query_params.get("code")
                out['status'] = 'refresh failed - get from code'
                #print('refresh failed - get from code'+auth_code)
                http, res = credentials_from_code(auth_code, flow, user, auth_uri)
                out['error'] = res['error']
                out['status'] = res['status']
                print(res['error'], res['status'])

    # credention not exist in db
    except ObjectDoesNotExist:
        auth_code = request.query_params.get("code")
        out['status'] = 'not exist in db - get new from code'
        #print('Get credentials from code: ',auth_code)
        http, res = credentials_from_code(auth_code, flow, user, auth_uri)
        out['error'] = res['error']
        out['status'] = res['status']
        print(res['error'],res['status'])

    if http is not None:
        if calendars:
            print('Get calendars from google')
            return create_calendars_from_api(user, http=http)
        if events:
            return create_events_from_api(user, http=http)
        if accesses:
            # TODO: make utilities for accesses
            return None
        if contacts:
            return create_contacts_from_api(user, http=http)
        if freebusy:
            return create_freebusy_from_api(user, http=http)
        if to_google:
            # build the API service to calendar v3 with authorized credentials
            service = build('calendar', 'v3', http=http)
            return service
    else:
        return out


def credentials_from_code(auth_code, flow, user, auth_uri):
    '''
     2 step google aithorisation :
     old function without email  - for one account only
    '''
    res = {'http': False,
           'auth_uri':auth_uri,
           'status':None,
           'token':None,
           'error':None}
    http = None
    # err = None
    if auth_code:
        # TODO: make exceptions for random code or already used code.
        try:
            credentials = flow.step2_exchange(code=auth_code, http=None)
            json_credentials = credentials.to_json()
            # print('access_token: ', credentials.access_token)
            res['token'] = credentials.access_token
            UserCredentials.objects.update_or_create(
                user=user,
                defaults={"json_credentials": json_credentials}
            )
            res['status'] = 'successfully exchange code'
        except Exception as e:
            err = "Credential code invalid: "+str(e)
            print(e)
            res['error'] = err
            res['status'] = 'Error exchanging code'
            return http, res

        try:
            http = credentials.authorize(httplib2.Http())
            res['http'] = True
            res['status'] = 'Successfully make credentials'
            return http, res
        except Exception as e:
            err = "Authorization failed: " + str(e)
            print(e)
            # return {"error": err}
            res['error'] = err
            return http, res
    else:
        #return {'error': "Auth.code failed :"+auth_uri}
        res['status'] = "No auth.code given :"+auth_uri
        res['error'] = " Auth.code failed :"+auth_uri
        return http, res


def cred_from_code(auth_code, user, email, auth_uri, flow):
    '''
     second step of google authorisation - get credentials from given code
     for multiple google accounts of user

    '''
    res = {'http': False,
           'auth_uri':auth_uri,
           'status':None,
           'token':None,
           'error':None}
    http = None
    # err = None
    if auth_code:
        # TODO: make exceptions for random code or already used code.
        try:
            credentials = flow.step2_exchange(code=auth_code, http=None)
            json_credentials = credentials.to_json()
            # print('access_token: ', credentials.access_token)
            res['token'] = credentials.access_token
            UserCredentials.objects.update_or_create(
                user=user, email = email,
                defaults={"json_credentials": json_credentials}
            )
            res['status'] = 'Successfully exchange code'
        except Exception as e:
            err = "Credential code invalid: "+str(e)
            print(err)
            res['error'] = err
            res['status'] = 'Error exchanging code: '+auth_code
            return http, res
        try:
            http = credentials.authorize(httplib2.Http())
            res['http'] = True
            res['status'] = 'Successfully make credentials'
            return http, res
        except Exception as e:
            err = "Authorization failed: " + str(e)
            print(e)
            # return {"error": err}
            res['error'] = err
            return http, res
    else:
        #return {'error': "Auth.code failed :"+auth_uri}
        res['status'] = "No auth.code given "
        res['error'] = " Auth.code failed - No auth.code given "
        return http, res

def get_cred (user, email, flow=None):
    '''
     get google credentilas from db and update if need
      - work only with existing old credentials!
    '''
    out = {'credentials': False,
              'auth_uri':None,
                'status':None,
                 'error':None}
    http = None
    if flow is None:
        flow = create_flow_from_settings()
    auth_uri = flow.step1_get_authorize_url() # step1 - here we get NEW code !!!
    out['auth_uri']= auth_uri
    # print(auth_uri)
    if 'error' in auth_uri:
        err = auth_uri.split('?')[1]
        print('Error in first step authorization: '+err)
        out['error'] = err
    try:
        current_user_creds = UserCredentials.objects.get(user=user,email=email)
        credential_object = client.Credentials.new_from_json(json_data=current_user_creds.json_credentials)
        out['status'] = 'Get credentials from db'
        if not credential_object.access_token_expired: # token exist and not expired
            try:
                http = credential_object.authorize(httplib2.Http())
                out['status'] = 'Authorization on google success'
                print('Authorization on google success')
                out['credentials'] = True
            # TODO: try to handle exception for expired token that cannot refresh
            except Exception as e:
                err = str(e)
                out['status'] = 'Authorize on google failed'
                print('authorize failed', err)
                out['error'] = err

        else:  # token exist and expired
            try:
                credential_object.refresh(httplib2.Http())
                out['status'] = 'Refresh credentials on google success'
                print('Refresh credentials on google success')
                http = credential_object.authorize(httplib2.Http())
                #  update ceredential if change in db
                json_credentials = credential_object.to_json()
                UserCredentials.objects.update_or_create(
                    user=user,email=email,
                    defaults={"json_credentials": json_credentials}
                )
                #return http, out
            except HttpAccessTokenRefreshError as e:
                out['status'] = 'Refresh token failed'
                out['error'] = str(e)
                print('Refresh token failed')
                print('error', out['error'])
                #return http, out

    # credention not exist in db
    except ObjectDoesNotExist:
        out['error'] = 'Credentials not exist in db'
        out['status'] = 'Credentials not exist in db'
        print(out['error'])

    return http, out
