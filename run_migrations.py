import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cpnfig.settings')
django.setup()

try:
    print("--- Running makemigrations ---")
    call_command('makemigrations')
    print("--- Running migrate ---")
    call_command('migrate')
    print("--- Successfully migrated! ---")
except Exception as e:
    print(f"Error during migration: {e}")
