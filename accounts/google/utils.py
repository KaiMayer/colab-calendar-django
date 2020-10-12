import httplib2
import json
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError
from googleapiclient.discovery import build

from outbizzed.settings.base import GOOGLE_CLIENT_SECRET, GOOGLE_SCOPES


def create_google_link_from_settings(need_flow=False):
    flow = OAuth2WebServerFlow(
        client_id=GOOGLE_CLIENT_SECRET["CLIENT_ID"],
        client_secret=GOOGLE_CLIENT_SECRET["CLIENT_SECRET"],
        scope=GOOGLE_SCOPES["GOOGLE_LOGIN"],
        redirect_uri=GOOGLE_CLIENT_SECRET["GOOGLE_LOGIN_REDIRECT"]
    )
    auth_uri = flow.step1_get_authorize_url()
    # request = httplib2.Http().request(auth_uri)
    if need_flow:
        return flow
    return auth_uri


def build_service_from_flow_and_code(flow=None, code=None):
    if flow is None:
        flow = create_google_link_from_settings(need_flow=True)
    if code is None:
        return {"error": "not found code"}
    try:
        credentials = flow.step2_exchange(code=code, http=None)
        http = credentials.authorize(httplib2.Http())
        service = build('people', 'v1', http=http)
    except FlowExchangeError:
        return {"error": "code already redeemed or it's incorrect"}
    return service


def make_google_api_query(service=None):
    if service is None:
        return {"error": "not found service"}
    elif type(service) is dict:
        if service['error']:
            return service
    else:
        response = service.people().get(resourceName="people/me", personFields="names,emailAddresses").execute()
        print(response)
        return response
