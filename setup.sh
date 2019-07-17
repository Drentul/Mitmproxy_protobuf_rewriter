#!/bin/bash

set +e

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

export PYTHON_PROTO_PATH="$VIRTUAL_ENV/lib/python3.6/site-packages/proto_py/"

cd ../proto

rm -rf "$PYTHON_PROTO_PATH"

mkdir -p "$PYTHON_PROTO_PATH"

IFS=$'\n'; set -f #This is needed for processing files and dirs with space ' ' symbol
dirs=`find . -maxdepth 1 -mindepth 1 -type d`
for dir in $dirs
do
    for file in `find "$dir" -type f -name '*.proto'`
        do
            mkdir -p "$PYTHON_PROTO_PATH${dir##*/}" #This is for creating dir only for proto files there
            protoc --proto_path="$dir" --python_out="$PYTHON_PROTO_PATH${dir##*/}" "$file"
        done
done
unset IFS; set +f

cp ../init.py "$PYTHON_PROTO_PATH/__init__.py"
set -

cd ..
git ls-files -z 'proto/' | xargs -0 git update-index --assume-unchanged
git ls-files -z 'data/' | xargs -0 git update-index --assume-unchanged

echo "Installation is finished"
echo "Now you can start working with mitmpoxy and rewrite addon usind '. run_mitm.sh'"

read -n 1 -p "Press any key to exit"
deactivate
return
