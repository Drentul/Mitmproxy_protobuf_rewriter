'''Add some lines to venv activate file'''

with open('venv/bin/activate', 'r') as f:
    TEXT = f.read()

INSERTION = 'if [ -n "${_OLD_VIRTUAL_PYTHONPATH:-}" ] ;\n    then PYTHONPATH="${_OLD_VIRTUAL_PYTHONPATH:-}"\n    export PYTHONPATH\n    unset _OLD_VIRTUAL_PYTHONPATH\nfi\n'

with open('venv/bin/activate', 'w') as f:
    for line in TEXT.splitlines():
        line += '\n'
        if line == 'deactivate () {\n':
            f.write(line+INSERTION)
        else:
            f.write(line)
    f.write('export _OLD_VIRTUAL_PYTHONPATH="$PYTHONPATH"\n')
    f.write('export PYTHONPATH="$VIRTUAL_ENV/lib/python3.6/site-packages:$PYTHONPATH"')
