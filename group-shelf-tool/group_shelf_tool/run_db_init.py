from group_bookshelf_tool import Config
config = Config()
log = config.set_logger(__package__, __name__)

import os
import sys
from group_bookshelf_tool.components.db_init import run_db_init


if __name__ == "__main__":
    run_db_init()

