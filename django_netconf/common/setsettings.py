import os
import sys

from django.core.management import settings
from django import setup as django_setup


def set_settings():
    """
    Adds django_netconf project to sys.path (PATH) if it is not already there
    :return: None
    """
    if not settings.configured:
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(project_path)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_netconf.config.settings')
        django_setup()