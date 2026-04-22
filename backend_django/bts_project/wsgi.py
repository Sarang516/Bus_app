"""
bts_project/wsgi.py  –  WSGI config for bts_project
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bts_project.settings")

application = get_wsgi_application()
