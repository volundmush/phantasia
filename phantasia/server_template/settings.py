from phantasia.settings_default import *







######################################################################
# Settings given in secret_settings.py override those in this file.
# They're meant to store critical things like secret keys and passwords etc.
######################################################################
try:
    from . secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")