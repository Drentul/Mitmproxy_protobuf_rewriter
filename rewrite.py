'''
The addon is used to rewrite the content of passing traffic.
In this file only sets paths to other files (data, configs, etc)
and initiates the addon.
'''
import rewrite_core

# Way to addons configuration file
CONFIG_FILE_PATH = 'data/config.json'
# Way to files which is used to replace content
REWRITING_DIR = 'data/fake_server'
# Way to savings folder
SAVING_DIR = 'data/saves'
# Way to api rules files
API_RULES_DIR = 'data/api_rules'

addons = [
    rewrite_core.Rewriter(CONFIG_FILE_PATH, SAVING_DIR,
                          REWRITING_DIR, API_RULES_DIR)
]
