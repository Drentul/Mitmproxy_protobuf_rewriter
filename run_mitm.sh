#!/bin/bash
. ./mitmproxy/venv/bin/activate
mitmproxy -w last_session -s rewrite.py
deactivate
