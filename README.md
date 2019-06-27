# Rewriter

This is the add-on for mitmproxy <https://github.com/mitmproxy/mitmproxy> project

## Setup

Clone this repo and than run following script:  

bash:  
```
. setup.sh
```

And follow the tips displayed in the console  

## Run proxy

Runs proxy by this script

bash:
```
. run_mitm.sh
```

if you want only proxy, without rewrite addon, comment (#) this "-s rewrite.py" in *run_mitm.sh* file

## Controls

The data needed to manage the add-on are in the /data folder.

**/data/config.json** - The file contains a set of rules specified in the json format. They are used to define actions that will be performed on passing requests. Actions such as: changing the headers, response code, saving or rewriting the content, adding a delay.

Format of one rule:
'''
[
  {
   "is_on": true,							//OPTIONAL: default: true
   "delay": 3,								//OPTIONAL: default: 0 //In seconds
   "authority_expr": "example.com",			//OPTIONAL: default: any
   "path_expr": "/example_path",			//OPTIONAL: default: any
   "method": ["GET"],						//OPTIONAL: default: ["GET", "POST", "PUT", "DELETE"]
   "save_content": "some_name.txt",			//OPTIONAL: default: None
   "rewrite_content": "SampleRewrite",		//OPTIONAL: default: None
   "status_code": 200,						//OPTIONAL: default: None
   "headers": {								//OPTIONAL: default: None
    "Content-Type": "Peace_of_cake"
   }
  }
]
'''

Notes:
Saving will occur as "some_name<counter>.txt", where counter is 1, 2, 3... and so on.

Updating this file will restart the addon with new configs

**/data/saves** - The default folder where the contents of the requests can be saved.

**/proto** - Contains .proto files describing protobuf messages. It is necessary to know for the correct interpretation of messages encoded in this format in the contents of messages between the client and the server. Place in this folder your oun proto files from your project.

**/data/fake_server** - This folder contains descriptions of specific protobuff messages in json format. By default, this path contains files used to rewrite the contents of requests.

**/data/api\_rules/\*.json** - These files contain mapping rules for server api and protobuff messages that can be sent in these requests. Each file contains the domain name of one or several servers, a list of possible error messages (of which the message type will be selected for encoding/decoding if the request was completed with an unsuccessful code), and a set of rules matching addresses and message types. The message type is defined by two parameters: "proto\_message" is a string parameter containing the name of the protobuff message. "module" is an optional string parameter, where the path to connect the module is specified, where this message can be found. A module is usually specified to avoid name conflicts. Please note that although the path is specified in the same way as the files are in the "/proto" folder, the "." symbol is a separator, and there is a \_pb2 postfix on the end. The files themselves in this folder can be called whatever you like, but must have the content in the format set by json.

For tips on managing proxies, see the project description https://github.com/mitmproxy/mitmproxy
