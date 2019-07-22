'''
Protobuf python sources are located at
'mitmproxy/venv/lib/python3.6/site-packages/proto_py' path
They are importes automatically by from proto_py import *
'''

import asyncio
import os
import re
import json
import time
from os import listdir, unlink
from os.path import isfile, join, dirname, exists, splitext
from urllib.parse import urlparse
from google.protobuf import json_format
from proto_py import *
from mitmproxy import http
from mitmproxy.script import concurrent
from mitmproxy import ctx


# By this name we can find this addon in addon manager
script_name = 'rewrite.py'
ReloadInterval = 1


def reload_addon():
    '''Func reloads this addon'''

    addon = ctx.master.addons.get('scriptmanager:' + script_name)
    addon.loadscript()


def find_free_name_in_path(full_path: str) -> str:
    directory = dirname(full_path)
    if not exists(directory):
        os.makedirs(directory)
    counter = 1
    file_name, file_extension = splitext(full_path)
    while True:
        changed_path = file_name + str(counter) + file_extension
        if not exists(changed_path):
            return changed_path
        counter = counter + 1


def to_camel_case(snake_str: str) -> str:
    '''Translates snake_case style string to camelCase style'''

    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def camel_json(json_file) -> None:
    '''Recursively iterates json for all dictionary keys in it
    and translates into camelCase'''

    for key in json_file:
        if isinstance(json_file, dict):
            new_key = to_camel_case(key)
            sub_js = json_file[new_key] = json_file.pop(key)

        if isinstance(json_file, list):
            sub_js = key

        if isinstance(sub_js, (dict, list)):
            camel_json(sub_js)


def rewrite_body_by_json(flow_response_or_request, json_obj, msg_types) -> None:
    '''Method rewrites content in request or response by
    json encoded to protobuf object of specified type'''

    msg = None
    for msg_type in msg_types:
        try:
            msg = msg_type()
            json_format.Parse(
                json.dumps(json_obj),
                msg,
                ignore_unknown_fields=False)
            break
        except json_format.ParseError:
            continue
    flow_response_or_request.content = msg.SerializeToString()


def find_protobuf_message_class(api_rule: dict):
    '''Method finds protobuf message that is eligible to api rules'''

    proto_message = api_rule.get('proto_message', None)
    if proto_message == 'text':
        return proto_message
    module = api_rule.get('module', None)

    for message in clsmembers:
        if (message.__name__ == proto_message and
                (module is None or message.__module__ == module)):
            return message
    return None


def find_errors_protobuf_messages(api_rule: dict) -> list:
    '''Method finds protobuf messages for errors from this api rule'''

    errors = api_rule.get("errors")
    if errors is None:
        return None
    errors_list = []

    for error in errors:
        err = find_protobuf_message_class(error)
        if err is not None:
            errors_list.append(err)
    return errors_list


class Rewriter:
    '''Class for capturing and rewriting some requests and responses'''

    def __init__(self, config_file_path: str, saving_dir: str,
                 rewriting_dir: str, api_rules_dir: str,
                 example_config_file_path: str, example_rewriting_dir: str,
                 example_api_rules_dir: str):

        if (os.path.isfile(config_file_path)):
            self.config_file_path = config_file_path
            self.rewriting_dir = rewriting_dir
            self.api_rules_dir = api_rules_dir
        else:
            self.config_file_path = example_config_file_path
            self.rewriting_dir = example_rewriting_dir
            self.api_rules_dir = example_api_rules_dir

        with open(self.config_file_path) as config:
            self.config_json = json.load(config)

        self.saving_dir = saving_dir

        # Такая структура нужна для возможности потом перезаписать файлы
        # так как они использовалсь в качестве источников
        self.api_map = [] # list of tuples [(json, string_file_name), ..]
        api_files = [f for f in listdir(self.api_rules_dir) if
                     isfile(join(self.api_rules_dir, f))]
        for api_file in api_files:
            with open(join(self.api_rules_dir, api_file)) as json_api_rule:
                self.api_map.append((json.load(json_api_rule), api_file))

        self.reloadtask = None
        self.reloadtask = asyncio.ensure_future(self.watcher())

    def done(self):
        '''This method runs at the end of the addons life'''
        if self.reloadtask:
            self.reloadtask.cancel()

    async def watcher(self):
        '''Method watches for some conditions, than calls addon reload'''
        last_mtime = 0
        while True:
            try:
                mtime = os.stat(self.config_file_path).st_mtime
            except FileNotFoundError:
                ctx.log.info('Removing script' + script_name)
                scripts = list(ctx.options.scripts)
                scripts.remove('rewrite.py')
                ctx.options.update(scripts=scripts)
                return
            if last_mtime == 0:
                last_mtime = mtime
            if mtime > last_mtime:
                reload_addon()

            await asyncio.sleep(ReloadInterval)

    def save_api_map(self) -> None:
        '''Method saves api map to files'''

        # Remove all files
        for the_file in listdir(self.api_rules_dir):
            file_path = join(self.api_rules_dir, the_file)
            try:
                if isfile(file_path):
                    unlink(file_path)
            except Exception as e:
                ctx.log.info(e)

        # Creating files and writes jsons to it
        for api in self.api_map:
            with open(join(self.api_rules_dir, api[1]), 'w+') as api_file:
                json.dump(api[0], api_file, indent=4)

    def add_rule_to_config_json(self, rule) -> None:
        '''Method adds rule to config'''

        pass

    def remove_rule_from_config(self, rule) -> None:
        '''Method removes rule from config'''

        pass

    def update_rule_in_config(self, rule) -> None:
        '''Method changes rule in config'''

        pass

    def save_config(self) -> None:
        '''Method saves config with rules'''

        with open(self.config_file_path) as config:
            json.dump(self.config_json, config)

    def find_rule(self, flow: http.HTTPFlow) -> dict:
        '''Method searches for rule in config, that
        is match to current request. Then returns this rule as dictionary.'''

        url = urlparse(flow.request.pretty_url)
        url_authority = url.netloc.split(':', 1)[0]
        url_path = url.path

        for rule in self.config_json:
            is_on = rule.get('is_on', True)
            is_match_authority = re.match(rule.get('authority_expr',
                                                   '.*'), url_authority)
            is_match_path = re.match('^/*' + rule.get('path_expr', '.*'
                                                      ) + '$', url_path)
            is_match_method = flow.request.method in\
                rule.get('method', ["GET", "POST", "PUT", "DELETE"])

            if not(
                   is_on and
                   is_match_authority and
                   is_match_path and
                   is_match_method):
                continue

            return rule
        return None

    def find_api(self, flow: http.HTTPFlow) -> dict:
        '''Method searches for API in config (api_map), that
        is match to current request. Then returns this API as dictionary.'''

        url = urlparse(flow.request.pretty_url)
        url_authority = url.netloc.split(':', 1)[0]
        url_path = url.path
        method = flow.request.method

        for api in self.api_map:
            if url_authority not in api[0].get('server'):
                continue
            rules = api[0].get('rules')
            for rule in rules:
                if (re.match('^/*' + rule.get('path', '') + '$', url_path) and
                        re.match(rule.get('method', '.*'), method)):
                    return_rule = rule
                    return_rule.update({"errors": api[0].get("errors")})
                    return return_rule
        return None

    # ctx.log.info почему-то несовместим с конкурентом ???
    # А нужен ли конкурент? https://discourse.mitmproxy.org/t/logging-and-threads/834
    @concurrent
    def request(self, flow: http.HTTPFlow) -> None:
        '''Method calls when the full HTTP request has been read
        It searches for the eligible rule in config
        and then replaces request content according to it'''

        rule = self.find_rule(flow)
        if rule is None:
            return

        # Bad internet settings: delay, loss

        delay = rule.get('delay', None)
        if delay not in (None, ''):
            time.sleep(delay)

    # @concurrent
    def response(self, flow: http.HTTPFlow) -> None:
        '''Method calls when the full HTTP response has been read
        It searches for the eligible rule in config
        and then replaces response content according to it'''

        rule = self.find_rule(flow)
        if rule is None:
            return

        status_code = rule.get('status_code', None)
        if status_code not in (None, ''):
            flow.response.status_code = status_code

        headers = rule.get('headers', None)
        if headers is not None:
            for header in headers:
                flow.response.headers[header] = headers.get(header)

        if rule.get('save_content', None) in (None, '') and\
                rule.get('rewrite_content', None) in (None, ''):
            return

        api_rule = self.find_api(flow)
        if api_rule is None:
            ctx.log.error("Can't find api rule for this request: "
                          + flow.request.pretty_url + ". Please check it in "
                          + self.api_rules_dir + " directory.")
            return

        errors_msg_types = find_errors_protobuf_messages(api_rule)

        protobuf_msg_type = find_protobuf_message_class(api_rule)
        if protobuf_msg_type is None:
            ctx.log.error("Can't find protobuf message for this request: "
                          + flow.request.pretty_url + ". Please check it in "
                          + self.api_rules_dir + " directory.")
            return

        # Save block

        save_content_path = rule.get('save_content', None)
        if save_content_path not in (None, ''):
            # Finding free path for saving
            full_path = join(self.saving_dir, save_content_path)
            free_path = find_free_name_in_path(full_path)

            # Saving process
            if protobuf_msg_type == 'text':
                content = flow.response.text
            else:
                protobuf_message = protobuf_msg_type()
                protobuf_message.ParseFromString(flow.response.content)
                json_obj = json_format.MessageToJson(protobuf_message,
                                                     preserving_proto_field_name=True)
                content = json_obj.encode().decode("unicode-escape")

            with open(free_path, "w") as save_file:
                save_file.write(content)

        # Rewrite block

        rewrite_content_path = rule.get('rewrite_content', None)
        if rewrite_content_path not in (None, ''):
            # Rewriting process
            with open(join(self.rewriting_dir,
                      rewrite_content_path)) as content_file:
                if protobuf_msg_type == 'text':
                    text = content_file.read()
                    flow.response.text = text
                else:
                    json_obj = json.load(content_file)
                    camel_json(json_obj)

                    if 200 <= flow.response.status_code < 300 or not ERRORS:
                        msg_types = [protobuf_msg_type]
                    else:
                        msg_types = errors_msg_types

                    rewrite_body_by_json(flow.response, json_obj, msg_types)
