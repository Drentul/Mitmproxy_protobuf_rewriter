In this folder there are number of protobuf message files (.proto) places in subdirectories.  

'example' - is a test folder with some files which is used for testing compile and import and as a tip for expected file structure. You may not delete this folder because it will be ignored if there is any else here. Simply place your own project with protobuf files inside another subfolder.  

This files compiles to '../mitmproxy/venv/lib/python3.6/site-packages/proto_py' and then from this place it is imports to main code.  

If possible, avoid overlapping names that could lead to conflict.  
