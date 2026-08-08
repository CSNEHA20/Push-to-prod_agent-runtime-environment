import sys
import os

# Ensure sdk directory is prioritized in sys.path over root repository directory
sdk_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if sdk_dir in sys.path:
    sys.path.remove(sdk_dir)
sys.path.insert(0, sdk_dir)
