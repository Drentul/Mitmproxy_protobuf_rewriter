"""
The addon is used to rewrite the content of passing traffic.
In this file only initiates the addon object
"""

import rewrite_core
from conf import *

addons = [
    rewrite_core.Rewriter(CONFIG_FILE_PATH, SAVING_DIR,
                          REWRITING_DIR, API_RULES_DIR,
                          EXAMPLE_CONFIG_FILE_PATH, EXAMPLE_REWRITING_DIR,
                          EXAMPLE_API_RULES_DIR)
]
