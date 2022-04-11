import datetime as dt
from unittest.mock import patch

import pytest
from celery.exceptions import Retry

from speid.models import Transaction
from speid.tasks.transactions import (
    process_outgoing_transactions,
    retry_incoming_transactions,
    send_transaction_status,
)
from speid.types import Estado, EventType
from speid.validations import SpeidTransaction
from tests.conftest import SEND_STATUS_TRANSACTION_TASK


@pytest.fixture
def incoming_transactions():
    yield [
        {
            'InstitucionBeneficiaria': '90646',
            'InstitucionOrdenante': '40021',
            'FechaOperacion': '20200424',
            'ClaveRastreo': 'HSBC000081',
            'Monto': 1000.0,
            'NombreOrdenante': 'CARLOS JAIR  AGUILAR PEREZ',
            'TipoCuentaOrdenante': 40,
            'CuentaOrdenante': '021650040600992156',
            'RFCCurpOrdenante': 'AUPC890116DU0',
            'NombreBeneficiario': 'CARLOS JAIR CTA CUENCA',
            'TipoCuentaBeneficiario': 40,
            'CuentaBeneficiario': '646180157000000004',
            'RFCCurpBeneficiario': '',
            'ConceptoPago': 'Andy',
            'ReferenciaNumerica': 230420,
            'Empresa': 'TAMIZI',
        },
        {
            'InstitucionBeneficiaria': '90646',
            'InstitucionOrdenante': '90646',
            'FechaOperacion': '20200424',
            'ClaveRastreo': 'MIBO587683053420',
            'Monto': 850.0,
            'NombreOrdenante': 'OMAR FLORES CASTRO',
            'TipoCuentaOrdenante': 40,
            'CuentaOrdenante': '646180142500081321',
            'RFCCurpOrdenante': 'FOCO9810191K9',
            'NombreBeneficiario': 'Omar Flores Castro',
            'TipoCuentaBeneficiario': 40,
            'CuentaBeneficiario': '646180157055148681',
            'RFCCurpBeneficiario': 'ND',
            'ConceptoPago': 'omar prro',
            'ReferenciaNumerica': 3053420,
            'Empresa': 'TAMIZI',
        },
    ]

    Transaction.objects.delete()


@pytest.fixture
def outgoing_transaction():
    transaction_values = dict(
        concepto_pago='PRUEBA',
        institucion_ordenante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='40072',
        monto=2511,
        nombre_beneficiario='Ricardo Sánchez',
        tipo_cuenta_beneficiario=40,
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='go' + dt.datetime.now().strftime('%m%d%H%M%S'),
        version=1,
    )
    transaction_val = SpeidTransaction(**transaction_values)
    transaction = transaction_val.transform()
    transaction.save()

    yield transaction

    transaction.delete()


def test_outgoing_transaction_succeeded(
    outgoing_transaction, mock_callback_queue
):
    speid_id = outgoing_transaction.speid_id
    to_process = [dict(speid_id=speid_id, action='succeeded')]
    process_outgoing_transactions(to_process)

    transaction = Transaction.objects.get(speid_id=speid_id)
    assert transaction.estado is Estado.succeeded


def test_outgoing_transaction_failed(
    outgoing_transaction, mock_callback_queue
):
    speid_id = outgoing_transaction.speid_id
    to_process = [dict(speid_id=speid_id, action='failed')]
    process_outgoing_transactions(to_process)

    transaction = Transaction.objects.get(speid_id=speid_id)
    assert transaction.estado is Estado.failed
    assert (
        len(
            [
                event
                for event in transaction.events
                if event.type is EventType.error
            ]
        )
        == 1
    )

    process_outgoing_transactions(to_process)
    transaction = Transaction.objects.get(speid_id=speid_id)
    assert transaction.estado is Estado.failed
    assert (
        len(
            [
                event
                for event in transaction.events
                if event.type is EventType.error
            ]
        )
        == 1
    )


def test_outgoing_transaction_invalid(
    outgoing_transaction, mock_callback_queue
):
    speid_id = outgoing_transaction.speid_id
    to_process = [dict(speid_id=speid_id, action='invalid')]

    with pytest.raises(ValueError):
        process_outgoing_transactions(to_process)


def test_outgoing_transaction_doesnotexist(outgoing_transaction):
    speid_id = outgoing_transaction.speid_id
    to_process = [dict(speid_id='RANDOM', action='succeeded')]
    process_outgoing_transactions(to_process)

    transaction = Transaction.objects.get(speid_id=speid_id)
    assert transaction.estado is Estado.created


def test_outgoing_transaction_retry_core(
    outgoing_transaction, mock_callback_queue
):
    speid_id = outgoing_transaction.speid_id
    with patch(
        'speid.tasks.transactions.Transaction.confirm_callback_transaction'
    ) as method_mock:
        retry_incoming_transactions(speid_ids=[speid_id])
    method_mock.assert_called_once()


@patch('celery.Celery.send_task')
def test_send_transaction_restricted_accounts_with_rfc(
    mock_send_task, outcome_transaction, moral_account, orden_pago
):
    moral_account.is_restricted = True
    moral_account.save()

    with patch('stpmex.client.Client.post', return_value=orden_pago):
        send_transaction_status(outcome_transaction.id)

    outcome_transaction.reload()
    mock_send_task.assert_called_with(
        SEND_STATUS_TRANSACTION_TASK,
        kwargs=dict(
            speid_id=outcome_transaction.speid_id,
            state=outcome_transaction.estado.value,
            rfc=orden_pago['ordenPago']['rfcCurpBeneficiario'],
            curp=None,
        ),
    )


@patch('celery.Celery.send_task')
def test_send_transaction_restricted_accounts_with_curp(
    mock_send_task, outcome_transaction, moral_account, orden_pago
):
    moral_account.is_restricted = True
    moral_account.save()

    orden_pago['ordenPago']['rfcCurpBeneficiario'] = 'AAAA951020HMCRQN00'

    with patch('stpmex.client.Client.post', return_value=orden_pago):
        send_transaction_status(outcome_transaction.id)

    outcome_transaction.reload()
    mock_send_task.assert_called_with(
        SEND_STATUS_TRANSACTION_TASK,
        kwargs=dict(
            speid_id=outcome_transaction.speid_id,
            state=outcome_transaction.estado.value,
            rfc=None,
            curp=orden_pago['ordenPago']['rfcCurpBeneficiario'],
        ),
    )


@patch('celery.Celery.send_task')
def test_send_transaction_restricted_accounts_invalid_rfc_curp(
    mock_send_task, outcome_transaction, moral_account, orden_pago
):
    moral_account.is_restricted = True
    moral_account.save()

    orden_pago['ordenPago']['rfcCurpBeneficiario'] = 'NA'

    with patch('stpmex.client.Client.post', return_value=orden_pago):
        send_transaction_status(outcome_transaction.id)

    outcome_transaction.reload()
    mock_send_task.assert_called_with(
        SEND_STATUS_TRANSACTION_TASK,
        kwargs=dict(
            speid_id=outcome_transaction.speid_id,
            state=outcome_transaction.estado.value,
            rfc=None,
            curp=None,
        ),
    )


@patch('celery.Celery.send_task')
def test_send_transaction_restricted_accounts_retry_task(
    mock_send_task, outcome_transaction, moral_account, orden_pago
):
    moral_account.is_restricted = True
    moral_account.save()

    orden_pago['ordenPago']['rfcCurpBeneficiario'] = None

    with patch('stpmex.client.Client.post', return_value=orden_pago):
        with pytest.raises(Retry):
            send_transaction_status(outcome_transaction.id)

    mock_send_task.assert_not_called()


@patch('celery.Celery.send_task')
def test_send_transaction_restricted_accounts_retry_task_on_unhandled_response(
    mock_send_task, outcome_transaction, moral_account, orden_pago
):
    moral_account.is_restricted = True
    moral_account.save()

    orden_pago['ordenPago']['rfcCurpBeneficiario'] = None

    with patch(
        'stpmex.client.Client.post',
        side_effect=Exception('something went wrong'),
    ):
        with pytest.raises(Retry):
            send_transaction_status(outcome_transaction.id)

    mock_send_task.assert_not_called()


@patch('speid.tasks.transactions.send_transaction_status.request.retries', 30)
@patch('celery.Celery.send_task')
def test_send_transaction_restricted_accounts_send_status_on_last_retry_task(
    mock_send_task, outcome_transaction, moral_account, orden_pago
):
    moral_account.is_restricted = True
    moral_account.save()

    orden_pago['ordenPago']['rfcCurpBeneficiario'] = None

    with patch('stpmex.client.Client.post', return_value=orden_pago):
        send_transaction_status(outcome_transaction.id)

    mock_send_task.assert_called_with(
        SEND_STATUS_TRANSACTION_TASK,
        kwargs=dict(
            speid_id=outcome_transaction.speid_id,
            state=outcome_transaction.estado.value,
            rfc=None,
            curp=None,
        ),
    )


@patch('celery.Celery.send_task')
def test_send_transaction_restricted_transaction_does_not_exist(
    mock_send_task,
):
    send_transaction_status('624f53b45809fa4d49258a57')
    mock_send_task.assert_not_called()


@patch('celery.Celery.send_task')
def test_send_transaction_not_restricted_accounts(
    mock_send_task, outcome_transaction, moral_account, orden_pago
):
    with patch('stpmex.client.Client.post', return_value=orden_pago):
        send_transaction_status(outcome_transaction.id)

    outcome_transaction.reload()
    mock_send_task.assert_called_with(
        SEND_STATUS_TRANSACTION_TASK,
        kwargs=dict(
            speid_id=outcome_transaction.speid_id,
            state=outcome_transaction.estado.value,
            rfc=None,
            curp=None,
        ),
    )


@patch('celery.Celery.send_task')
def test_send_transaction_not_restricted_accounts_persona_fisica(
    mock_send_task, outcome_transaction, physical_account, orden_pago
):
    with patch('stpmex.client.Client.post', return_value=orden_pago):
        send_transaction_status(outcome_transaction.id)

    outcome_transaction.reload()
    mock_send_task.assert_called_with(
        SEND_STATUS_TRANSACTION_TASK,
        kwargs=dict(
            speid_id=outcome_transaction.speid_id,
            state=outcome_transaction.estado.value,
            rfc=None,
            curp=None,
        ),
    )
