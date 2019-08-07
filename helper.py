'''
Helper script that contains a number
of useful functions to the main code.
'''

import os.path
import json
from google.protobuf import json_format
from proto_py import *
from mitmproxy import ctx


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
    '''Rewrites content in request or response by
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


def save_body_as_json(flow_response_or_request, protobuf_msg_type) -> str:
    '''Turns flow body from protobuf to string for saving'''

    protobuf_message = protobuf_msg_type()
    protobuf_message.ParseFromString(flow_response_or_request.content)
    ctx.log.info('faf')
    json_obj = json_format.MessageToJson(protobuf_message,
                                         preserving_proto_field_name=True)
    ctx.log.info('aaaa')
    return json_obj.encode().decode("unicode-escape")


def find_protobuf_message_class(api_rule: dict):
    '''Finds protobuf message that is eligible to api rules'''

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
    '''Finds protobuf messages for errors from this api rule'''

    errors = api_rule.get("errors")
    if errors is None:
        return None
    errors_list = []

    for error in errors:
        err = find_protobuf_message_class(error)
        if err is not None:
            errors_list.append(err)
    return errors_list


def find_free_name_in_path(full_path: str) -> str:
    '''Finds free name for saving by counting name with adding counter'''
    directory = os.path.dirname(full_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    counter = 1
    file_name, file_extension = os.path.splitext(full_path)
    while True:
        changed_path = file_name + str(counter) + file_extension
        if not os.path.exists(changed_path):
            return changed_path
        counter = counter + 1
