import json
import logging

from flask import request
from mongoengine import NotUniqueError
from sentry_sdk import capture_exception

from speid import app
from speid.config import (
    CREATE_ORDER_URL,
    SUCCESSFUL_RESPONSE_KEY,
    SUCCESSFUL_RESPONSE_VALUE,
    UPDATE_ORDER_URL,
)
from speid.models import Event, Transaction
from speid.models.helpers import base62_uuid
from speid.processors import backend_client
from speid.tasks.orders import send_order
from speid.types import Estado
from speid.utils import post, put
from speid.validations import StpTransaction, UpdateSpeidTransaction

logging.basicConfig(level=logging.INFO, format='SPEID: %(message)s')


@app.route('/')
@app.route('/healthcheck')
def health_check():
    return "I'm healthy!"


@app.route(UPDATE_ORDER_URL, methods=['POST'])
def create_orden_events():
    try:
        transaction = Transaction.objects.get(stp_id=request.json['id'])
        state = Estado.get_state_from_stp(request.json['Estado'])
        transaction.detalle = str(request.json.get('Detalle', ''))

        if state is Estado.failed:
            assert transaction.estado is not Estado.failed

        transaction.set_status(state)
        update_request = UpdateSpeidTransaction(
            id=transaction.speid_id,
            empresa=transaction.empresa,
            estado=state,
        )
        backend_client.update_order(update_request)

        transaction.save()
    except Exception as exc:
        capture_exception(exc)

    return "got it!"


@post(CREATE_ORDER_URL)
def create_orden():
    transaction = Transaction()
    try:
        abono = request.json['abono']
        external_tx = StpTransaction(**abono)  # type: ignore
        transaction = external_tx.transform()
        transaction.estado = Estado.succeeded
        transaction.save()
        backend_client.receive_order(request.json)
        response = request.json
        response[SUCCESSFUL_RESPONSE_KEY] = SUCCESSFUL_RESPONSE_VALUE
    except (NotUniqueError, TypeError) as e:
        response = {SUCCESSFUL_RESPONSE_KEY: SUCCESSFUL_RESPONSE_VALUE}
        capture_exception(e)
    except Exception as e:
        response = {SUCCESSFUL_RESPONSE_KEY: SUCCESSFUL_RESPONSE_VALUE}
        transaction.estado = Estado.error
        transaction.save()
        Event(target_document_id=str(transaction.id), metadata=str(e)).save()
        transaction.save()
        capture_exception(e)
    return 201, response


@put('/registra')
def incoming_order():
    body = request.json
    body['speid_id'] = base62_uuid('SP')()
    response = dict(resultado=dict(id=body['speid_id'], data=request.json))
    send_order.apply_async(kwargs={'order_values': body})
    return 201, response


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
