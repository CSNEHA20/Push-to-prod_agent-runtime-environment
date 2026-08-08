import sys
import os

# Ensure sdk directory is prioritized in sys.path over root repository directory
sdk_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_dir = os.path.abspath(os.path.join(sdk_dir, ".."))

if root_dir in sys.path:
    sys.path.remove(root_dir)

if sdk_dir in sys.path:
    sys.path.remove(sdk_dir)

sys.path.insert(0, sdk_dir)

# Remove cached 'arc' module if it was loaded from root directory
if "arc" in sys.modules:
    del sys.modules["arc"]
