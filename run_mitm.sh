#!/bin/bash
. ./mitmproxy/venv/bin/activate
mitmproxy -s rewrite.py
deactivate
