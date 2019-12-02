"""
Protobuf python sources are located at
'mitmproxy/venv/lib/python3.6/site-packages/proto_py' path
They are imports automatically by from proto_py import *
"""

import asyncio
import json
import os
import re
import time
from os import listdir, unlink
from urllib.parse import urlparse

from mitmproxy import ctx
from mitmproxy import http
from mitmproxy.script import concurrent

import GUI
import helper

# FIX: After the first reboot of the addon, the closure of the gui breaks


# By this name we can find this addon in addon manager
script_name = 'rewrite.py'
ReloadInterval = 1


def reload_addon() -> None:
    """Func reloads this addon"""

    addon = ctx.master.addons.get('scriptmanager:' + script_name)
    addon.loadscript()


async def watch(config_file_path):
    """Task watches for some conditions, than calls addon reload"""
    last_mtime = 0
    while True:
        try:
            mtime = os.stat(config_file_path).st_mtime
        except FileNotFoundError:
            ctx.log.info('Removing script' + script_name)
            scripts = list(ctx.options.scripts)
            scripts.remove('rewrite.py')
            ctx.options.update(scripts=scripts)
            return
        if last_mtime == 0:
            last_mtime = mtime
        if mtime > last_mtime:
            last_mtime = mtime  # Don't need to repeat this steps
            reload_addon()

        await asyncio.sleep(ReloadInterval)


class SingletonWatcher(object):
    """Singleton class for running watching
    task that reloads addon by the condition"""

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SingletonWatcher, cls).__new__(cls)
        return cls.instance

    def start(self, config_file_path):
        self.task = asyncio.ensure_future(watch(config_file_path))

    def stop(self):
        if self.task:
            self.task.cancel()


singleton_watcher = SingletonWatcher()


class Rewriter:
    """Class for capturing and rewriting some requests and responses"""

    def __init__(self, config_file_path: str, saving_dir: str,
                 rewriting_dir: str, api_rules_dir: str,
                 example_config_file_path: str, example_rewriting_dir: str,
                 example_api_rules_dir: str):

        ctx.log.info('Creating addon object')
        has_error_in_init = False

        if os.path.isfile(config_file_path):
            self.config_file_path = config_file_path
            self.rewriting_dir = rewriting_dir
            self.api_rules_dir = api_rules_dir
        else:
            self.config_file_path = example_config_file_path
            self.rewriting_dir = example_rewriting_dir
            self.api_rules_dir = example_api_rules_dir

        try:
            with open(self.config_file_path) as config:
                try:
                    self.config_json = json.load(config)
                except json.JSONDecodeError:
                    ctx.log.error(f'Cannot decode json config in {self.config_file_path}, please check it.')
                    has_error_in_init = True
        except EnvironmentError:
            ctx.log.error(f'File {self.config_file_path} not found. It is needed to work with the addon.')
            has_error_in_init = True

        self.saving_dir = saving_dir

        self.api_map = []  # list of tuples [(json, string_file_name), ..]
        api_files = [f for f in listdir(self.api_rules_dir) if
                     os.path.isfile(os.path.join(self.api_rules_dir, f))]
        for api_file in api_files:
            try:
                with open(os.path.join(self.api_rules_dir, api_file)) as json_api_rule:
                    try:
                        api_rule = json.load(json_api_rule)
                    except json.JSONDecodeError:
                        # Excluding invalid configs with error
                        ctx.log.error(f'Cannot decode json config in {os.path.join(self.api_rules_dir, api_file)}'
                                      f', please check it.')
                        continue
                    self.api_map.append((api_rule, api_file))
            except EnvironmentError:
                # Unnecessary exception. We compile a list of files according to data from the system.
                # They must exist
                ctx.log.error(f'File {os.path.join(self.api_rules_dir, api_file)} not found.'
                              f' It is needed to work with the addon.')
                has_error_in_init = True

        singleton_watcher.start(self.config_file_path)  # Temporarily disabled
        ctx.log.info('Created new reloading watcher')

        if has_error_in_init:
            ctx.log.error(f'Cannot load the addon {script_name}.'
                          f' See the error above.')
            addon = ctx.master.addons.get('scriptmanager:' + script_name)
            ctx.master.addons.remove(addon)
            return

        #self.gui = GUI.GUI(self, self.config_json, self.api_map)
        #ctx.log.info("Created new GUI")

    def done(self):
        """This method runs at the end of the addons life"""
        #if self.gui is not None and self.gui.isAlive():
        #    self.gui.close()
        #    self.gui.join()
        singleton_watcher.stop()
        ctx.log.info('Closing addon function. Stops all.')

    def save_api_map(self) -> None:
        """Method saves api map to files"""

        # Remove all files
        for the_file in listdir(self.api_rules_dir):
            file_path = os.path.join(self.api_rules_dir, the_file)
            try:
                if os.path.isfile(file_path):
                    unlink(file_path)
            except Exception as e:
                ctx.log.info(e)

        # Creating files and writes jsons to it
        for api in self.api_map:
            with open(os.path.join(self.api_rules_dir, api[1]), 'w+') as api_file:
                json.dump(api[0], api_file, indent=4)

    def find_api(self, flow: http.HTTPFlow) -> dict:
        """Method searches for API in config (api_map), that
        is match to current request. Then returns this API as dictionary."""

        url = urlparse(flow.request.pretty_url)
        url_authority = url.netloc.split(':', 1)[0]
        url_path = url.path
        method = flow.request.method

        for api_and_name in self.api_map:
            is_server_found = False  # Flag for searching

            api = api_and_name[0]

            for server in api.get('server'):
                if re.match(server, url_authority):
                    is_server_found = True

            if not is_server_found:
                continue

            rules = api.get('rules')

            for rule in rules:
                if (re.match('^/*' + rule.get('path', '.*') + '$', url_path) and
                        re.match(rule.get('method', '.*'), method)):
                    return_rule = rule.copy()
                    return_rule.update({"errors": api[0].get("errors")})
                    return return_rule
        return None

    def save_config(self) -> None:
        """Method saves config with rules"""

        with open(self.config_file_path, 'w+') as config:
            json.dump(self.config_json, config, indent=4)

    def find_rule(self, flow: http.HTTPFlow) -> dict:
        """Method searches for rule in config, that
        is match to current request. Then returns this rule as a dictionary."""

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

# Needs to do something with async. Concurrent is a treat to overflow.
    @concurrent
    def request(self, flow: http.HTTPFlow) -> None:
        """Method calls when the full HTTP request has been read
        It searches for the eligible rule in config
        and then replaces request content according to it"""

        rule = self.find_rule(flow)
        if rule is None:
            return

        # Bad internet settings: delay, loss

        delay = rule.get('delay', None)
        if delay not in (None, ''):
            time.sleep(delay)

    def response(self, flow: http.HTTPFlow) -> None:
        """Method calls when the full HTTP response has been read
        It searches for the eligible rule in config
        and then replaces response content according to it"""

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

        errors_msg_types = helper.find_errors_protobuf_messages(api_rule)

        protobuf_msg_type = helper.find_protobuf_message_class(api_rule)
        if protobuf_msg_type is None:
            ctx.log.error("Can't find protobuf message for this request: "
                          + flow.request.pretty_url + ". Please check it in "
                          + self.api_rules_dir + " directory.")
            return

        # Save block

        save_content_path = rule.get('save_content', None)
        if save_content_path not in (None, ''):
            # Finding free path for saving
            full_path = os.path.join(self.saving_dir, save_content_path)
            free_path = helper.find_free_name_in_path(full_path)

            # Saving process
            if protobuf_msg_type == 'text':
                content = flow.response.text
            else:
                content = helper.save_body_as_json(flow.response,
                                                   protobuf_msg_type)

            with open(free_path, "w") as save_file:
                save_file.write(content)

        # Rewrite block

        rewrite_content_path = rule.get('rewrite_content', None)
        if rewrite_content_path not in (None, ''):
            # Rewriting process
            with open(os.path.join(self.rewriting_dir,
                      rewrite_content_path)) as content_file:
                if protobuf_msg_type == 'text':
                    text = content_file.read()
                    flow.response.text = text
                else:
                    json_obj = json.load(content_file)
                    helper.camel_json(json_obj)

                    if 200 <= flow.response.status_code < 300 or not errors_msg_types:
                        msg_types = [protobuf_msg_type]
                    else:
                        msg_types = errors_msg_types

                    helper.rewrite_body_by_json(flow.response, json_obj, msg_types)
