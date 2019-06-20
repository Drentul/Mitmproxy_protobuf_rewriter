'''
Protobuf python sources are located at 
'mitmproxy/venv/lib/python3.6/site-packages/proto_py' path
They are importes automatically by from proto_py import *
But when using, you also need to specify the subfolders such as:
  vod.v2.vod_pb2.VODCollection()
'''

import re
import json
import time
import os.path
from urllib.parse import urlparse
from google.protobuf import json_format
from proto_py import *
from mitmproxy import http
from mitmproxy.script import concurrent
from mitmproxy import ctx

'''
Represents the API map of the messeges between application and server.
It establishes a correspondence between the path used and the return type of the protobuff message.

"proto_type":"text" - This is a special modifier showing that the body of the request will return text message.
'''

API_MAP = [
    {
        "path":"/static/.*.json",
        "method":"GET",
        "proto_type":"text"
    },
    {
        "path":"vod/v2/",
        "method":"GET",
        "proto_type":vod.v2.vod_pb2.VODCollection
    },
    {
        "path":"/auth/v1/with-verified-contacts/available-logins",
        "method":"GET",
        "proto_type":auth.v1.available_logins_pb2.AvailableLogins
    },
    {
        "path":"/app-info",
        "method":"GET",
        "proto_type":general_pb2.AppInfoV2
    },
    {
        "path":"/v2/account",
        "method":"GET",
        "proto_type":accounts_pb2.Account
    },
    {
        "path":"/login",
        "method":"POST",
        "proto_type":user_pb2.User
    },
    {
        "path":"/login/qr",
        "method":"GET",
        "proto_type":user_pb2.User
    },
    {
        "path":"/logout",
        "method":"GET",
        "proto_type":message_pb2.Message
    },
    {
        "path":"/account/change-profile",
        "method":"GET",
        "proto_type":message_pb2.Message
    },
    {
        "path":"/channels",
        "method":"GET",
        "proto_type":epg_pb2.EPG
    },
    {
        "path":"/walls/0",
        "method":"GET",
        "proto_type":recommendations_pb2.MainWall
    },
    {
        "path":"/walls/1",
        "method":"GET",
        "proto_type":recommendations_pb2.PersonalContentWall
    },
    {
        "path":"/purchase-info",
        "method":"GET",
        "proto_type":purchases_pb2.PurchaseInfos
    },
    {
        "path":"/playback-info/[^/]*",
        "method":"GET",
        "proto_type":playback_pb2.LivePlaybackInfo
    },
    {
        "path":"/channels/[^/]*/programs",
        "method":"GET",
        "proto_type":epg_pb2.EPG
    },
    {
        "path":"/pauses/[^/]*",
        "method":"GET",
        "proto_type":playback_pb2.ChannelPauses
    },
    {
        "path":"/v2/settings/profile/restrictions",
        "method":"GET",
        "proto_type":accounts_pb2.ProfileRestrictions
    }
    ,
    {
        "path":"/vod/v2/archive/titles/[^/]*/episodes",
        "method":"GET",
        "proto_type":vod.v2.vod_pb2.VODEpisodes
    },
    {
        "path":"/vod/v2/archive/titles/[^/]*",
        "method":"GET",
        "proto_type":vod.v2.vod_pb2.VODTitle
    },
    {
        "path":"/pause/vod/v1/titles/archive/[^/]*",
        "method":"GET",
        "proto_type":pauses.v1.pauses_pb2.VODPauses
    }
]

'''
List of possible errors. It uses in case of return code not in 2xx.
Than applies the first suitable message listed below if this list is not empty.
'''

ERRORS = [general_pb2.HttpFormErrors, general_pb2.HttpError]

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

        if isinstance(json_file, list):
            sub_js = key

        if isinstance(sub_js, (dict, list)):
            camel_json(sub_js)

def rewrite_body_by_json(flow_response_or_request, json_object, msg_types) -> None:
    '''Method rewrites content in request or response by
    json encoded to protobuf object of specified type'''

    msg = None
    for msg_type in msg_types:
        try:
            msg = msg_type()
            json_format.Parse(\
                json.dumps(json_object),\
                msg,\
                ignore_unknown_fields=False)
            break
        except json_format.ParseError:
            continue
    flow_response_or_request.content = msg.SerializeToString()

class Rewriter:
    '''Class for capturing and rewriting some requests and responses'''

    def __init__(self, jsonString: str, saving_dir: str, rewriting_dir: str):
        self.config_json = json.loads(jsonString)
        self.saving_dir = saving_dir
        self.rewriting_dir = rewriting_dir
        self.api_map = API_MAP

    def find_rule(self, flow: http.HTTPFlow) -> dict:
        '''Method searches for rule in config, that
        is match to current request. Then returns this rule as dictionary.'''

        url = urlparse(flow.request.pretty_url)
        url_authority = url.netloc.split(':', 1)[0]
        url_path = url.path

        for rule in self.config_json:
            is_on = rule.get('is_on', True)
            is_match_authority = re.match(rule.get('authority_expr', '.*'), url_authority)
            is_match_path = re.match('^/*' + rule.get('path_expr', '.*') + '$', url_path)
            is_match_method = flow.request.method in\
                rule.get('method', ["GET", "POST", "PUT", "DELETE"])

            if not(\
                is_on and\
                is_match_authority and\
                is_match_path and\
                is_match_method):
                continue

            return rule
        return None

    def find_api(self, flow: http.HTTPFlow) -> dict:
        '''Method searches for API in config, that
        is match to current request. Then returns this API as dictionary.'''

        url = urlparse(flow.request.pretty_url)
        url_path = url.path

        for api in self.api_map:
            if (re.match('^/*' + api.get('path', '') + '$', url_path) and\
                re.match(api.get('method', '.*'), flow.request.method)):
                return api
        return None

    @concurrent
    def request(self, flow: http.HTTPFlow) -> None:
        '''Method calls when the full HTTP request has been read
        It searches for the eligible rule in config
        and then replaces request content according to it'''

        rule = self.find_rule(flow)
        if rule is None:
            return

        #Bad internet settings: delay, loss

        delay = rule.get('delay', None)
        if not delay in (None, ''):
            time.sleep(delay)

    def response(self, flow: http.HTTPFlow) -> None:
        '''Method calls when the full HTTP response has been read
        It searches for the eligible rule in config
        and then replaces response content according to it'''

        rule = self.find_rule(flow)
        if rule is None:
            return

        status_code = rule.get('status_code', None)
        if not status_code in (None, ''):
            flow.response.status_code = status_code

        headers = rule.get('headers', None)
        if headers != None:
            for header in headers:
                flow.response.headers[header] = headers.get(header)

        api = self.find_api(flow)
        protobuf_msg_type = api.get('proto_type')

        #Save block

        save_content_path = rule.get('save_content', None)
        if not save_content_path in (None, ''):
            #Finding free path for saving
            full_path = os.path.join(self.saving_dir, save_content_path)
            directory = os.path.dirname(full_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            counter = 1
            file_name, file_extension = os.path.splitext(full_path)
            while True:
                changed_path = file_name + str(counter) + file_extension
                if not os.path.exists(changed_path):
                    break
                counter = counter + 1

            #Saving process
            if protobuf_msg_type == 'text':
                content = flow.response.text
            else:
                protobuf_message = protobuf_msg_type()
                protobuf_message.ParseFromString(flow.response.content)
                json_obj = json_format.MessageToJson(protobuf_message, preserving_proto_field_name=True)
                content = json_obj.encode().decode("unicode-escape")

            with open(changed_path, "w") as save_file:
                save_file.write(content)

        #Rewrite block

        rewrite_content_path = rule.get('rewrite_content', None)
        if not rewrite_content_path in (None, ''):
            #Rewriting process
            with open(os.path.join(self.rewriting_dir, rewrite_content_path)) as content_file:
                if protobuf_msg_type == 'text':
                    text = content_file.read()
                    flow.response.text = text
                else:
                    json_obj = json.load(content_file)
                    camel_json(json_obj)

                    if 200 <= flow.response.status_code < 300 or not ERRORS:
                        msg_types = [protobuf_msg_type]
                    else:
                        msg_types = ERRORS

                    rewrite_body_by_json(flow.response, json_obj, msg_types)
