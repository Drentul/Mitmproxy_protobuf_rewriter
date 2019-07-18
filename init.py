from importlib import import_module
from os.path import dirname, normpath, sep, basename, relpath, split, join
from os import walk
import inspect
import sys

root_path = dirname(__file__)
subdirs = next(walk(root_path))[1]

for subdir in subdirs:
    module_path = join(root_path, subdir)
    if ((module_path not in sys.path) & (subdir != '__pycache__')):
        sys.path.append(module_path)

# r=root, d=directories, f = files
clsmembers = []
for r, d, f in walk(dirname(__file__)):
    if '__pycache__' in d:
        d.remove('__pycache__')
    if ((r == dirname(__file__)) & (len(d) > 1) & ('example' in d)):
        d.remove('example')
    import_path = normpath(relpath(r, split(dirname(__file__))[0])).replace(sep, '.')
    for _file in f:
        if _file.endswith('.py') and not _file.endswith('__init__.py'):
            module = import_module('.' + basename(_file)[:-3], import_path)
            for class_with_name in inspect.getmembers(module, inspect.isclass):
                clsmembers.append(class_with_name[1])
