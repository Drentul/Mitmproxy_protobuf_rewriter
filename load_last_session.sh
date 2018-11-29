#!/bin/bash
. ./mitmproxy/venv/bin/activate
mitmproxy -n -r last_session
deactivate
