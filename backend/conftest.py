import os
import sys
import django
from pathlib import Path

# Add backend directory to Python path
backend_path = str(Path(__file__).resolve().parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
