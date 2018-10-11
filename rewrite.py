''' The addon is used to rewrite the content of passing traffic.
It is configured in json file.
The file sets a set of rules, according to which the content of the requests is changed.
Use regexp syntax for it in fields: authority_expr, path_expr
https://docs.python.org/2/library/re.html - regexp in 're' python library

Example:

[
  {
   "is_on": true,
   "authority_expr": "fe.smotreshka.tv",
   "path_expr": "/playback-info",
   "method": ["GET"],
   "replace_response": {
    "status_code": 100,
    "headers": {
     "value": "key"
    },
    "body": "Example"
   }
  }
]

Note that each request may response error one of theese types
HttpFormErrors or HttpError
Status code must not be 200
Its proto messages structure is:

message HttpFormError {
    required string name = 1;
    required string msg  = 2;
}

message HttpFormErrors {
    repeated HttpFormError errors = 1;
}

message HttpError {
	required int32  code = 1;
	required string msg  = 2;
    optional string message = 3;
}'''
#from  mitmproxy.addons 
import rewrite_core

#Way to files which is used to replace content
WORKING_DIR = 'fake_server'

CONFIG = \
'''
[
  {
   "path_expr": "/app-info",
   "method": ["GET"],
   "replace_response": {
    "status_code": 400,
    "headers": {
     "Content-Type": "fucking_various_bytes",
     "aaaAAAA":"11313",
     "dasadsa":"dd",
     "qqqqqqqqq":"qq"
    },
    "body": "Error"
   }
  },
  {
   "path_expr": "/v2/account",
   "method": ["GET"],
   "replace_response": {
    "headers": {
     "Content-Type": "application/my",
     "aaaAAAA":"11313",
     "dasadsa":"dd",
     "qqqqqqqqq":"qq"
    },
    "body": "Account"
   }
  }
]
'''

addons = [
    rewrite_core.Rewriter(CONFIG, WORKING_DIR)
]
