''' The addon is used to rewrite the content of passing traffic.
It is configured in json file.
The file sets a set of rules, according to which the content of the requests is changed.
Use regexp syntax for it in fields: authority_expr, path_expr
https://docs.python.org/2/library/re.html - regexp in 're' python library

////////////////////////////////////////////////////////////////////////

Example:

[
  {
   "is_on": true,							//OPTIONAL: default: true
   "authority_expr": "fe.smotreshka.tv",	//OPTIONAL: default: any
   "path_expr": "/playback-info",			//OPTIONAL: default: any
   "method": ["GET"],						//OPTIONAL: default: ["GET", "POST", "PUT", "DELETE"]
   "save_content": "playback/some_name.txt",//OPTIONAL: default: None
   "rewrite_content": "LivePlaybackInfo",	//OPTIONAL: default: None
   "status_code": 200,						//OPTIONAL: default: None
   "headers": {								//OPTIONAL: default: None
    "Content-Type": "Peace_of_cake"
   }
  }
]

If there is "playback/some_name<counter>.txt", where counter is 1, 2, 3... and so on.

////////////////////////////////////////////////////////////////////////

FOR COPY & PASTE!

  {
   "is_on": true,
   "authority_expr": "fe.smotreshka.tv",
   "path_expr": "/playback-info",
   "method": ["GET"],
   "save_content": "playback/some_name.txt",
   "rewrite_content": "LivePlaybackInfo",
   "status_code": 200,
   "headers": {
    "Content-Type": "Peace_of_cake"
   }
  }

////////////////////////////////////////////////////////////////////////

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
import rewrite_core

#Way to files which is used to replace content
REWRITING_DIR = 'fake_server'
SAVING_DIR = 'saves'

CONFIG = \
'''
[
  {
   "path_expr": "/static/basic_settings.json",
   "method": ["GET"],
   "save_content": "bsic/basic_settings.json",
   "rewrite_content": "",
   "status_code": 200,
   "headers": {
   }
  },
  {
   "path_expr": "/app-info",
   "method": ["GET"],
   "save_content": "appinfo",
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
