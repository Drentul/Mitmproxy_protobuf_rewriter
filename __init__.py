from importlib import import_module
from os.path import dirname, normpath, sep, basename, relpath, split
from os import walk

# r=root, d=directories, f = files
for r, d, f in walk(dirname(__file__)):
    import_path = normpath(relpath(r, split(dirname(__file__))[0])).replace(sep, '.')
    for _file in f:
        if _file.endswith('.py') and not _file.endswith('__init__.py'):
            import_module('.' + basename(_file)[:-3], import_path)
