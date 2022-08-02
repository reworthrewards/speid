__all__ = [
    'STP_EMPRESA',
    'backend_client',
    'config',
    'commands',
    'models',
    'views',
]

import datetime as dt
import json
from enum import Enum

import sentry_sdk
from flask import Flask
from flask_mongoengine import MongoEngine
from python_hosts import Hosts, HostsEntry
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.flask import FlaskIntegration

from .config import DATABASE_URI, SENTRY_DSN, SENTRY_ENVIRONMENT


class CJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            encoded = o.name
        elif isinstance(o, dt.datetime):
            encoded = o.isoformat() + 'Z'
        else:
            try:
                encoded = o.to_dict()
            except AttributeError:  # pragma: no cover
                encoded = super().default(o)
        return encoded


def configure_environment():
    from .config import EDIT_HOSTS, HOST_AD, HOST_IP

    # Edita archivo hosts si es necesario
    if EDIT_HOSTS == 'true':
        host_ip = HOST_IP
        host_ad = HOST_AD
        hosts = Hosts()
        new_entry = HostsEntry(
            entry_type='ipv4', address=host_ip, names=[host_ad]
        )
        hosts.add([new_entry])
        hosts.write()


# Configura sentry
sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=SENTRY_ENVIRONMENT,
    integrations=[FlaskIntegration(), CeleryIntegration()],
)

app = Flask('speid')

app.config['MONGODB_HOST'] = DATABASE_URI

app.json_encoder = CJSONEncoder  # type: ignore

db = MongoEngine(app)

configure_environment()

from . import (  # noqa: E402 isort:skip
    backend_client,
    commands,
    config,
    models,
    views,
)
