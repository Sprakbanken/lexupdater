import importlib.util
import sys

import config
FILE_PATH = config.__file__
MODULE_NAME = config.__name__

spec = importlib.util.spec_from_file_location(MODULE_NAME, FILE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
exec_module = getattr(spec.loader, "exec_module")
exec_module(module)

# Ensure the output directory exists
config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
