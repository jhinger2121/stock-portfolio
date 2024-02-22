import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'StockPortfolio.settings')

# key_file = '/tmp/keyfile.key'
# cert_file = '/tmp/certfile.crt'
# ca_file = '/tmp/CAtmp.pem'


app = Celery('StockPortfolio')
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'
# app.conf.redis_backend_use_ssl = {
#                  'ssl_keyfile': key_file, 'ssl_certfile': cert_file,
#                  'ssl_ca_certs': ca_file,
#                  'ssl_cert_reqs': 'CERT_REQUIRED'
#             }


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')