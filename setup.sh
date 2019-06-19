#!/bin/bash

IsLibInstalled()
{
which $1 >/dev/null
if ! [ "$?" = "0" ] ; then
    read -n 1 -p "(Please install $1 in your system. Press any key to exit.)"
    return
fi
}

echo "Running setup virtual environment"

IsLibInstalled "python3"
IsLibInstalled "protoc"

cd mitmproxy
. dev.sh

echo "Starting setup reqirments for addon to venv"

pip3 install -r ../requirements.txt

python3 ../add_pythonpath.py

export PYTHON_PROTO_PATH="$VIRTUAL_ENV/lib/python3.6/site-packages/proto_py"

cd ../frontendproto

mkdir -p $PYTHON_PROTO_PATH
protoc --proto_path . --python_out=$PYTHON_PROTO_PATH $(find .  -type f -name '*.proto')
cp ../__init__.py $PYTHON_PROTO_PATH
set -

echo "Installation is finished"
echo "Now you can start working with mitmpoxy and rewrite addon usind '. run_mitm.sh'"

read -n 1 -p "Press any key to exit"
deactivate
return
