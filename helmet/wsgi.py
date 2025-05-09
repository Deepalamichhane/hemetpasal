"""
WSGI config for helmet project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'helmetpasal.settings')

application = get_wsgi_application()
