# wsgi.py - PythonAnywhere specific version

import sys
import os

# PythonAnywhere path
path = '/home/yourusername/ff-proxy'  # CHANGE THIS TO YOUR PATH
if path not in sys.path:
    sys.path.append(path)

# Set database path for PythonAnywhere
os.environ['DB_PATH'] = '/tmp/proxy_hack.db'

from app import app as application