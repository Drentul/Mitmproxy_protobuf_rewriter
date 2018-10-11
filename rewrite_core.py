"""
GET /app-info AppInfoV2
GET /v2/account Account
POST /login Response:User
GET /login/qr Response:User
GET /logout Message
GET /account/change-profile Message
GET /channels EPG
GET /walls/0 MainWall
GET /walls/1 PersonalContentWall
GET /v2/account/services/purchases/cache/last-update PurchaseCacheLastUpdate
GET /purchase-info?type=live PurchaseInfos
GET /channels/[channelId]/programs?period=([start]:[end])|now EPG
GET /playback-info/[channelId] LivePlaybackInfo
GET /pauses/[channelId]?live=[bool] ChannelPauses
GET /v2/settings/profile/restrictions ProfileRestrictions
"""

import re
import json
from os.path import join
from urllib.parse import urlparse
from google.protobuf import json_format
from proto_py import general_pb2
from proto_py import accounts_pb2
from mitmproxy import http
#from mitmproxy import ctx

API_MAP = [
    {
        "path":"/app-info",
        "method":"GET",
        "proto_type":general_pb2.AppInfoV2()
    },
    {
        "path":"/v2/account",
        "method":"GET",
        "proto_type":accounts_pb2.Account()
    }
]

def to_camel_case(snake_str: str) -> str:
    '''Translates snake_case style string to camelCase style'''

    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def camel_json(json_file) -> None:
    '''Recursive iterate json for all dictionary keys in it and translate into camelCase'''

    for key in json_file:
        if isinstance(json_file, dict):
            new_key = to_camel_case(key)
            sub_js = json_file[new_key] = json_file.pop(key)
        if isinstance(sub_js, (dict, list)):
            camel_json(sub_js)

def rewrite_body_by_json(flow_response_or_request, json_object, message_type) -> None:
    '''Method rewrites content in request or response by
    json encoded to protobuf object of specified type'''

    flow_response_or_request.content = json_format.Parse(\
                    json.dumps(json_object),\
                    message_type,\
                    ignore_unknown_fields=False).SerializeToString()

class Rewriter:
    '''Class for capturing and rewriting some requests and responses'''

    def __init__(self, jsonString: str, working_dir: str):
        self.config_json = json.loads(jsonString)
        self.working_dir = working_dir

    def request(self, flow: http.HTTPFlow) -> None:
        '''Method calls when the full HTTP request has been read
        It searches for the eligible rule in config
        and then replaces request content according to it'''

        pass

    def response(self, flow: http.HTTPFlow) -> None:
        '''Method calls when the full HTTP response has been read
        It searches for the eligible rule in config
        and then replaces response content according to it'''

        url = urlparse(flow.request.pretty_url)
        url_authority = url.netloc.split(':', 1)[0]
        url_path = url.path

        for rule in self.config_json:
            match_authority = re.match(rule.get('authority_expr', '.*'), url_authority)
            match_path = re.match('/*' + rule.get('path_expr', '.*') + '$', url_path)
            method = rule.get('method', '.*')
            replace_response = rule.get('replace_response', None)

            if not(\
                rule.get('is_on', True) and\
                match_authority and\
                match_path and\
                flow.request.method in method and\
                replace_response != None):
                continue

            status_code = replace_response.get('status_code', None)
            if status_code != None:
                flow.response.status_code = status_code

            headers = replace_response.get('headers', None)
            if headers != None:
                for header in headers:
                    flow.response.headers[header] = headers.get(header)

            body = replace_response.get('body', None)
            if body is None:
                continue

            for api in API_MAP:
                if not (re.match('/*' + api.get("path", '') + '$', url_path) and\
                    re.match(api.get('method', '.*') + '$', flow.request.method)):
                    continue
                with open(join(self.working_dir, body)) as json_file:
                    json_obj = json.load(json_file)
                    camel_json(json_obj)
                    if flow.response.status_code == 200:
                        rewrite_body_by_json(flow.response, json_obj, api.get("proto_type"))
                        break
                    try:
                        rewrite_body_by_json(flow.response, json_obj, general_pb2.HttpFormErrors())
                    except json_format.ParseError:
                        rewrite_body_by_json(flow.response, json_obj, general_pb2.HttpError())
                break
