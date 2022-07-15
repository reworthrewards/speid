from unittest.mock import patch

import pytest

from speid.models import Event, Transaction
from speid.types import Estado


def test_ping(client):
    res = client.get('/')
    assert res.status_code == 200


def test_health_check(client):
    res = client.get('/healthcheck')
    assert res.status_code == 200


@pytest.mark.usefixtures('mock_backend')
def test_create_order_event(client, outcome_transaction):
    data = dict(
        id=outcome_transaction.stp_id,
        Estado='LIQUIDACION',
        Detalle="0",
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=outcome_transaction.id)
    assert trx.estado is Estado.succeeded


@pytest.mark.usefixtures('mock_backend')
def test_create_order_event_failed_twice(client, outcome_transaction):
    data = dict(
        id=outcome_transaction.stp_id, Estado='DEVOLUCION', Detalle="0"
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=outcome_transaction.id)
    assert trx.estado is Estado.failed

    num_events = Event.objects(target_document_id=str(trx.id)).count()
    data = dict(
        id=outcome_transaction.stp_id, Estado='DEVOLUCION', Detalle="0"
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=outcome_transaction.id)
    assert trx.estado is Estado.failed
    assert Event.objects(target_document_id=str(trx.id)).count() == num_events


@pytest.mark.usefixtures('mock_backend')
def test_cancelled_transaction(client, outcome_transaction) -> None:
    data = dict(
        id=outcome_transaction.stp_id,
        Estado='CANCELACION',
        Detalle='something went wrong',
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=outcome_transaction.id)
    assert trx.estado is Estado.failed
    assert trx.detalle == 'something went wrong'


def test_invalid_order_event(client, outcome_transaction):
    data = dict(Estado='LIQUIDACION', Detalle="0")
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=outcome_transaction.id)
    assert trx.estado is Estado.created


def test_invalid_id_order_event(client, outcome_transaction):
    data = dict(id='9', Estado='LIQUIDACION', Detalle="0")
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=outcome_transaction.id)
    assert trx.estado is Estado.created


@pytest.mark.usefixtures('mock_backend')
def test_order_event_duplicated(client, outcome_transaction):
    data = dict(
        id=outcome_transaction.stp_id,
        Estado='LIQUIDACION',
        Detalle="0",
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    data = dict(
        id=outcome_transaction.stp_id, Estado='DEVOLUCION', Detalle="0"
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=outcome_transaction.id)
    assert trx.estado is Estado.failed


@pytest.mark.usefixtures('mock_backend')
def test_create_orden(client, default_income_transaction):
    resp = client.post('/ordenes', json=default_income_transaction)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.succeeded
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'
    transaction.delete()


@pytest.mark.usefixtures('mock_backend')
def test_create_mal_formed_orden(client):
    request = {
        "Clave": 17658976,
        "ClaveRastreo": "clave-restreo",
        "CuentaOrdenante": "014180567802222244",
        "FechaOperacion": 20200416,
        "InstitucionBeneficiaria": 90646,
        "InstitucionOrdenante": 40014,
        "Monto": 500,
        "NombreOrdenante": "Pepito",
        "RFCCurpOrdenante": "XXXX950221141",
        "TipoCuentaOrdenante": 40,
    }
    resp = client.post('/ordenes', json=request)
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'


@pytest.mark.usefixtures('mock_backend')
def test_create_orden_duplicated(client, default_income_transaction):
    resp = client.post('/ordenes', json=default_income_transaction)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.succeeded
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'

    default_income_transaction['Clave'] = 2456304
    resp = client.post('/ordenes', json=default_income_transaction)
    transactions = Transaction.objects(
        clave_rastreo=default_income_transaction['abono']['claveRastreo']
    ).order_by('-created_at')
    assert len(transactions) == 1
    assert transactions[0].stp_id == 2456303
    assert transactions[0].estado is Estado.succeeded
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'
    for t in transactions:
        t.delete()


def test_create_orden_exception(client, default_income_transaction):
    with patch(
        'requests.Session.request', side_effect=Exception('Algo muy malo')
    ):
        resp = client.post('/ordenes', json=default_income_transaction)
        transaction = Transaction.objects.order_by('-created_at').first()
        assert transaction.estado is Estado.error
        assert resp.status_code == 201
        assert resp.json['estado'] == 'LIQUIDACION'
        transaction.delete()


@pytest.mark.usefixtures('mock_backend')
def test_create_orden_without_ordenante(client):
    data = dict(
        abono=dict(
            id=123123233,
            fechaOperacion=20190129,
            institucionOrdenante=40102,
            institucionBeneficiaria=90646,
            claveRastreo='MANU-00000295251',
            monto=1000,
            nombreOrdenante='null',
            tipoCuentaOrdenante=0,
            cuentaOrdenante='null',
            rfcCurpOrdenante='null',
            nombreBeneficiario='JESUS ADOLFO ORTEGA TURRUBIATES',
            tipoCuentaBeneficiario=40,
            cuentaBeneficiario='646180157020812599',
            rfcCurpBeneficiario='ND',
            conceptoPago='FONDEO',
            referenciaNumerica=1232134,
            empresa='TAMIZI',
        )
    )
    resp = client.post('/ordenes', json=data)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.succeeded
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'
    transaction.delete()
