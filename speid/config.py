import os

BACKEND_JWT_TOKEN = os.environ['BACKEND_JWT_TOKEN']
BACKEND_URL = os.environ['BACKEND_URL']
UPDATE_ORDER_URL = os.getenv('UPDATE_ORDER_URL', '/orden_events')
CREATE_ORDER_URL = os.getenv('CREATE_ORDER_URL', '/ordenes')
