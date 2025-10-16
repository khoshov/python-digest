#!/usr/bin/env python
"""
Configuration file for pytest.
This file is automatically loaded by pytest before running tests.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to sys.path
project_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(project_dir))

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Setup Django
django.setup()
