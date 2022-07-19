import os

BACKEND_JWT_TOKEN = os.environ['BACKEND_JWT_TOKEN']
BACKEND_URL = os.environ['BACKEND_URL']
UPDATE_ORDER_URL = os.getenv('UPDATE_ORDER_URL', '/orden_events')
CREATE_ORDER_URL = os.getenv('CREATE_ORDER_URL', '/ordenes')
EDIT_HOSTS = os.environ['EDIT_HOSTS']
HOST_IP = os.getenv('HOST_IP')
HOST_AD = os.getenv('HOST_AD')
SENTRY_DSN = os.environ['SENTRY_DSN']
SENTRY_ENVIRONMENT = os.environ['SENTRY_ENVIRONMENT']
STP_PRIVATE_KEY = os.environ['STP_PRIVATE_KEY']
STP_EMPRESA = os.environ['STP_EMPRESA']
DATABASE_URI = os.environ['DATABASE_URI']
STP_EMPRESA = os.environ['STP_EMPRESA']
STP_KEY_PASSPHRASE = os.environ['STP_KEY_PASSPHRASE']
STP_BASE_URL = os.getenv('STP_BASE_URL', None)
SPEID_ENV = os.getenv('SPEID_ENV', '')
AMPQ_ADDRESS = os.environ['AMPQ_ADDRESS']
CELERY_REGION = os.environ['CELERY_REGION']
CELERY_NAME_PREFIX = os.environ['CELERY_NAME_PREFIX']
