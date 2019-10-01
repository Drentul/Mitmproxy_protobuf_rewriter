"""
The addon is used to rewrite the content of passing traffic.
In this file only sets paths to other files (data, configs, etc)
and initiates the addon.
"""

import rewrite_core

# Way to addons configuration file

CONFIG_FILE_PATH = 'data/config.json'
# Way to example configuration file. Works only if config.json is absent
EXAMPLE_CONFIG_FILE_PATH = 'data/example_config.json'
# Way to files which is used to replace content
REWRITING_DIR = 'data/fake_server'
# Way to example fake server. Works only for example config
EXAMPLE_REWRITING_DIR = 'data/fake_server/example'
# Way to savings folder
SAVING_DIR = 'data/saves'
# Way to api rules files
API_RULES_DIR = 'data/api_rules'
# Name of example api rules file. Works only if there are no one other
EXAMPLE_API_RULES_DIR = 'data/api_rules/example'

addons = [
    rewrite_core.Rewriter(CONFIG_FILE_PATH, SAVING_DIR,
                          REWRITING_DIR, API_RULES_DIR,
                          EXAMPLE_CONFIG_FILE_PATH, EXAMPLE_REWRITING_DIR,
                          EXAMPLE_API_RULES_DIR)
]
