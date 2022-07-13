import json
import logging

from flask import request
from mongoengine import NotUniqueError
from sentry_sdk import capture_exception

from speid import app
from speid.models import Event, Transaction
from speid.processors import backend_client
from speid.tasks.orders import send_order
from speid.types import Estado
from speid.utils import post
from speid.validations import StpTransaction, UpdateSpeidTransaction

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
        update_request = UpdateSpeidTransaction(
            speid_id=transaction.speid_id,
            orden_id=transaction.stp_id,
            estado=state,
        )
        backend_client.update_order(update_request)

        transaction.save()
    except Exception as exc:
        capture_exception(exc)

    return "got it!"


@post('/ordenes')
def create_orden():
    transaction = Transaction()
    try:
        external_tx = StpTransaction(**request.json)  # type: ignore
        transaction = external_tx.transform()
        transaction.estado = Estado.succeeded
        transaction.save()
        backend_client.receive_order(external_tx)
        response = request.json
        response['estado'] = Estado.convert_to_stp_state(transaction.estado)
    except (NotUniqueError, TypeError) as e:
        response = dict(estado='LIQUIDACION')
        capture_exception(e)
    except Exception as e:
        response = dict(estado='LIQUIDACION')
        transaction.estado = Estado.error
        Event(target_document_id=str(transaction.id), metadata=str(e)).save()
        transaction.save()
        capture_exception(e)
    return 201, response


@post('/registra')
def incoming_order():
    send_order.apply_async(request.json)


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
