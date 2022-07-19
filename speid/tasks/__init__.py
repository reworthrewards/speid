from celery import Celery
from flask.app import Flask

from speid import app
from speid.config import AMPQ_ADDRESS, CELERY_NAME_PREFIX, CELERY_REGION


def make_celery(app: Flask) -> Celery:
    celery_app = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        include=[
            'speid.tasks.orders',
        ],
    )
    celery_app.conf.update(app.config)

    class ContextTask(celery_app.Task):  # type: ignore
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app


app.config['CELERY_BROKER_URL'] = AMPQ_ADDRESS
app.config['BROKER_TRANSPORT_OPTIONS'] = {
    'region': CELERY_REGION,
    'queue_name_prefix': CELERY_NAME_PREFIX
}

celery = make_celery(app)
