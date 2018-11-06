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
import os.path
from urllib.parse import urlparse
from google.protobuf import json_format
from proto_py.vod.v2 import vod_pb2
from proto_py import general_pb2
from proto_py import accounts_pb2
from proto_py import user_pb2
from proto_py import message_pb2
from proto_py import epg_pb2
from proto_py import recommendations_pb2
from proto_py import playback_pb2
from proto_py import purchases_pb2
from mitmproxy import http
from mitmproxy import ctx

#TODO: Царское туду
'''
Надо:
1) Пройтись по другой документации api, запустить приложение и чекнуть, что основные запросы покрыты
2) Дописать по необходимости
3) Описать реврайт реквеста
4) Посмотреть насколько удобно делать быстрые подмены - модифицировать хедеры
'''

API_MAP = [
    {
        "path":"/static/.*.json",
        "method":"GET",
        "proto_type":"text"
    },
    {
        "path":"/vod/v2/.*/titles.*",
        "method":"GET",
        "proto_type":vod_pb2.VODTitle()
    },
    {
        "path":"/app-info",
        "method":"GET",
        "proto_type":general_pb2.AppInfoV2()
    },
    {
        "path":"/v2/account",
        "method":"GET",
        "proto_type":accounts_pb2.Account()
    },
    {
        "path":"/login",
        "method":"POST",
        "proto_type":user_pb2.User()
    },
    {
        "path":"/login/qr",
        "method":"GET",
        "proto_type":user_pb2.User()
    },
    {
        "path":"/logout",
        "method":"GET",
        "proto_type":message_pb2.Message()
    },
    {
        "path":"/account/change-profile",
        "method":"GET",
        "proto_type":message_pb2.Message()
    },
    {
        "path":"/channels",
        "method":"GET",
        "proto_type":epg_pb2.EPG()
    },
    {
        "path":"/walls/0",
        "method":"GET",
        "proto_type":recommendations_pb2.MainWall()
    },
    {
        "path":"/walls/1",
        "method":"GET",
        "proto_type":recommendations_pb2.PersonalContentWall()
    },
    {
        "path":"/purchase-info",
        "method":"GET",
        "proto_type":purchases_pb2.PurchaseInfos()
    },
    {
        "path":"/playback-info/.*",
        "method":"GET",
        "proto_type":playback_pb2.LivePlaybackInfo()
    },
    {
        "path":"/channels/.*/programs",
        "method":"GET",
        "proto_type":epg_pb2.EPG()
    },
    {
        "path":"/pauses/.*",
        "method":"GET",
        "proto_type":playback_pb2.ChannelPauses()
    },
    {
        "path":"/v2/settings/profile/restrictions",
        "method":"GET",
        "proto_type":accounts_pb2.ProfileRestrictions()
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

    def __init__(self, jsonString: str, saving_dir: str, rewriting_dir: str):
        self.config_json = json.loads(jsonString)
        self.saving_dir = saving_dir
        self.rewriting_dir = rewriting_dir

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
            match_path = re.match('^/*' + rule.get('path_expr', '.*') + '$', url_path)
            method = rule.get('method', ["GET", "POST", "PUT", "DELETE"])

            if not(\
                rule.get('is_on', True) and\
                match_authority and\
                match_path and\
                flow.request.method in method):
                continue
                
            save_content_path = rule.get('save_content', None)
            if not save_content_path in (None, ''):
                full_path = os.path.join(self.saving_dir, save_content_path)
                ctx.log.info(full_path)
                directory = os.path.dirname(full_path)
                ctx.log.info(directory)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                counter = 1
                file_name, file_extension = os.path.splitext(full_path)
                while True:
                    changed_path = file_name + str(counter) + file_extension
                    if not os.path.exists(changed_path):
                        break
                    counter = counter + 1

                for api in API_MAP:
                    if not (re.match('^/*' + api.get('path', '') + '$', url_path) and\
                        re.match(api.get('method', '.*') + '$', flow.request.method)):
                        continue

                    if api.get('proto_type') == 'text':
                        content = flow.response.text
                    else:
                        msg = api.get('proto_type')
                        msg.ParseFromString(flow.response.content)
                        json_obj = json_format.MessageToJson(msg, preserving_proto_field_name=True)
                        content = json_obj.encode().decode("unicode-escape")
                        
                    with open(changed_path, "w") as save_file:
                            save_file.write(content)

            status_code = rule.get('status_code', None)
            if not status_code in (None, ''):
                flow.response.status_code = status_code

            headers = rule.get('headers', None)
            if headers != None:
                for header in headers:
                    flow.response.headers[header] = headers.get(header)

            rewrite_content_path = rule.get('rewrite_content', None)
            if rewrite_content_path in (None, ''):
                continue

            for api in API_MAP:
                if not (re.match('^/*' + api.get('path', '') + '$', url_path) and\
                    re.match(api.get('method', '.*') + '$', flow.request.method)):
                    continue

                with open(os.path.join(self.rewriting_dir, rewrite_content_path)) as content_file:
                    if api.get('proto_type') == 'text':
                        text = content_file.read()
                        flow.response.text = text
                        break
                    json_obj = json.load(content_file)
                    camel_json(json_obj)
                    if flow.response.status_code == 200:
                        rewrite_body_by_json(flow.response, json_obj, api.get('proto_type'))
                        break
                    try:
                        rewrite_body_by_json(flow.response, json_obj, general_pb2.HttpFormErrors())
                    except json_format.ParseError:
                        rewrite_body_by_json(flow.response, json_obj, general_pb2.HttpError())
                break
