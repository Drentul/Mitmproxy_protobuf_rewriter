''' The addon is used to rewrite the content of passing traffic.
It is configured in json below.
The json sets a number of rules, according to which the content of the requests is changed.

Use regexp syntax for it in fields: authority_expr, path_expr
https://docs.python.org/2/library/re.html - regexp in 're' python library

////////////////////////////////////////////////////////////////////////

Example:

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

Notes:
Saving will occur as "some_name<counter>.txt", where counter is 1, 2, 3... and so on.

////////////////////////////////////////////////////////////////////////

Please note that each request may return an error if the status code is not 2xx.
Define a list of possible error messages in the rewrite_core.py file.
'''
import rewrite_core

#Way to files which is used to replace content
REWRITING_DIR = 'fake_server'
#Way to savings folder
SAVING_DIR = 'saves'

#Config with come examples
CONFIG = \
'''
[
  {
   "path_expr": ".*sample/settings.json",
   "method": ["GET"],
   "save_content": "",
   "rewrite_content": "settings.json",
   "status_code": 200,
   "headers": {
   }
  },
  {
   "path_expr": "/single/item",
   "method": ["GET"],
   "rewrite_content": "Item_proto_message_as.json"
  },
  {
   "delay": 3,
   "path_expr": "/sample/image/info/.*",
   "method": ["GET"],
   "save_content": "image.json",
   "rewrite_content": "",
   "status_code": 200,
   "headers": {
   }
  }
]
'''

addons = [
    rewrite_core.Rewriter(CONFIG, SAVING_DIR, REWRITING_DIR)
]
