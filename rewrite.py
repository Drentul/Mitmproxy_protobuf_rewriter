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

FOR COPY & PASTE!

  {
   "is_on": true,
   "delay": 3,
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

Please note that each request may return an error if the status code is not 2xx.
Define a list of possible error messages in the rewrite_core.py file.

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

# Way to addons configuration file
CONFIG_FILE_PATH = 'data/config.json'
# Way to files which is used to replace content
REWRITING_DIR = 'data/fake_server'
# Way to savings folder
SAVING_DIR = 'data/saves'
# Way to api rules files
API_RULES_DIR = 'data/api_rules'

addons = [
    rewrite_core.Rewriter(CONFIG_FILE_PATH, SAVING_DIR,
                          REWRITING_DIR, API_RULES_DIR)
]
