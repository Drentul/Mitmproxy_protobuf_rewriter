#!/bin/bash

echo "Running setup virtual environment"

cd mitmproxy
. dev.sh

echo "Starting setup reqirments for addon to venv"

pip3 install -r ../requirements.txt

sed -i -e 's/^deactivate () {$/deactivate () {\n if [ -n "${_OLD_VIRTUAL_PYTHONPATH:-}" ] ;\n    then PYTHONPATH="${_OLD_VIRTUAL_PYTHONPATH:-}"\n    export PYTHONPATH\n    unset _OLD_VIRTUAL_PYTHONPATH\n fi/' $VIRTUAL_ENV/bin/activate

echo 'export _OLD_VIRTUAL_PYTHONPATH="$PYTHONPATH"
export PYTHONPATH="$VIRTUAL_ENV/lib/python3.6/site-packages/proto_py:$PYTHONPATH"' >> $VIRTUAL_ENV/bin/activate

export PYTHON_PROTO_PATH="$VIRTUAL_ENV/lib/python3.6/site-packages/proto_py"

cd ../frontendproto

mkdir -p $PYTHON_PROTO_PATH
protoc --proto_path . --python_out=$PYTHON_PROTO_PATH $(find .  -type f -name '*.proto')
