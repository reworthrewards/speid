import json
import logging

from flask import request
from sentry_sdk import capture_exception

from speid import app
from speid.helpers.transaction_helper import process_incoming_transaction
from speid.models import Event, Transaction
from speid.types import Estado
from speid.utils import post

logging.basicConfig(level=logging.INFO, format='SPEID: %(message)s')


@app.route('/')
@app.route('/healthcheck')
def health_check():
    return "I'm healthy!"


@app.route('/orden_events', methods=['POST'])
def create_orden_events():
    try:
        transaction = Transaction.objects.get(stp_id=request.json['id'])
        state = Estado.get_state_from_stp(request.json['Estado'])
        transaction.detalle = str(request.json.get('Detalle', ''))

        if state is Estado.failed:
            assert transaction.estado is not Estado.failed

        transaction.set_status(state)

        transaction.save()
    except Exception as exc:
        capture_exception(exc)

    return "got it!"


@post('/ordenes')
def create_orden():
    transaction = Transaction()
    try:
        external_tx = StpTransaction(request.json)  # type: ignore
        transaction = external_tx.transform()
        transaction.estado = Estado.succeeded
        transaction.confirm_callback_transaction()
        transaction.save()
        response = request.json
        response['estado'] = Estado.convert_to_stp_state(transaction.estado)
    except (NotUniqueError, TypeError) as e:
        response = dict(estado='LIQUIDACION')
        capture_exception(e)
    except Exception as e:
        response = dict(estado='LIQUIDACION')
        transaction.estado = Estado.error
        Event(target_document_id=transaction.pk, metadata=str(e)).save()
        transaction.save()
        capture_exception(e)
    return response


@app.after_request
def log_responses(response):
    data = None
    if response.data:
        data = response.data.decode()
        if response.json:
            data = json.loads(data)

    headers = [str(header) for header in response.headers]

    logging.info(f'{str(response)} {"".join(headers)} {str(data)}')
    return response


@app.before_request
def log_posts():
    if 'healthcheck' in request.path:
        return
    data = None
    if request.data:
        data = request.data.decode()
        if request.is_json:
            data = json.loads(data)
    headers = [
        str(header)
        for header in request.headers
        if 'Authorization' not in header
    ]

    logging.info(f'{str(request)} {"".join(headers)} {str(data)}')
