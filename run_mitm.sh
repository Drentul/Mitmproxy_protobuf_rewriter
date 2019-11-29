#!/bin/bash
. ./mitmproxy/venv/bin/activate
python3 dummyGUI.py &
mitmproxy -w last_session -s rewrite.py
deactivate
