import os
import sys
import site

site.addsitedir('/home/engineroom/.virtualenvs/kmonitor/lib/python2.7/site-packages')

# Add the app's directory to the PYTHONPATH
sys.path.append('/var/www/k-monitor')
sys.path.append('/var/www/k-monitor/crowdata')

os.environ['DJANGO_SETTINGS_MODULE'] = 'crowdata.settings'

# Activate your virtual env
activate_env=os.path.expanduser("/home/engineroom/.virtualenvs/kmonitor/bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))







import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
