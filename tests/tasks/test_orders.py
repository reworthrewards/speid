from unittest.mock import MagicMock, patch

import pytest

from speid.exc import MalformedOrderException, ResendSuccessOrderException
from speid.models import Transaction
from speid.tasks.orders import execute, retry_timeout, send_order
from speid.types import Estado


@pytest.mark.parametrize(
    'attempts, expected', [(1, 2), (5, 10), (10, 1200), (15, 1200)]
)
def test_retry_timeout(attempts, expected):
    assert retry_timeout(attempts) == expected


def test_malformed_order_worker(mock_backend):
    order = dict(
        speid_id='speid_id',
        empresa='empresa',
        concepto_pago='PRUEBA',
        institucion_ordenante='646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='072',
        monto=1020,
        nombre_beneficiario='Ricardo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        version=2,
    )
    with pytest.raises(MalformedOrderException):
        execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.error
    transaction.delete()


@pytest.mark.vcr
def test_create_order_debit_card():
    order = dict(
        concepto_pago='DebitCardTest',
        institucion_operante='90646',
        cuenta_beneficiario='4242424242424242',
        institucion_contraparte='40072',
        monto=1020,
        nombre_beneficiario='Pach',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='5694433',
        version=2,
    )
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    transaction.delete()


@pytest.mark.vcr
def test_worker():
    order = dict(
        concepto_pago='PRUEBA Version 2',
        institucion_operante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_contraparte='40072',
        monto=1020,
        nombre_beneficiario='Pablo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='ANOTHER_RANDOM_ID',
    )
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    transaction.delete()


def test_invalid_amount(mock_backend):
    order = dict(
        concepto_pago='PRUEBA Version 2',
        institucion_operante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_contraparte='40072',
        monto=-1020,
        nombre_beneficiario='Pablo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='ANOTHER_RANDOM_ID',
        empresa='EMPRESA',
        version=2,
    )
    send_order(order)

    transaction = Transaction.objects.order_by('-created_at').first()

    assert transaction.estado is Estado.failed
    assert transaction.speid_id == 'ANOTHER_RANDOM_ID'
    transaction.delete()


@patch('speid.tasks.orders.capture_exception')
def test_malformed_order_exception(
    mock_capture_exception: MagicMock, mock_backend
):
    order = dict(
        concepto_pago='PRUEBA Version 2',
        institucion_operante='90646',
        cuenta_beneficiario='123456789012345678',
        institucion_contraparte='40072',
        monto=1020,
        nombre_beneficiario='Pablo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='ANOTHER_RANDOM_ID',
        empresa='EMPRESA',
        version=2,
    )
    send_order(order)

    mock_capture_exception.assert_called_once()

    transaction = Transaction.objects.order_by('-created_at').first()
    transaction.delete()


@patch('speid.tasks.orders.execute', side_effect=Exception())
@patch('speid.tasks.orders.capture_exception')
@patch('speid.tasks.orders.send_order.retry')
def test_retry_on_unexpected_exception(
    mock_retry: MagicMock, mock_capture_exception: MagicMock, _
):
    order = dict(
        concepto_pago='PRUEBA Version 2',
        institucion_ordenante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='40072',
        monto=1020,
        nombre_beneficiario='Pablo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='ANOTHER_RANDOM_ID',
        version=2,
    )
    send_order(order)
    mock_retry.assert_called_once()
    mock_capture_exception.assert_called_once()


@pytest.mark.vcr
def test_resend_success_order():
    order = dict(
        concepto_pago='PRUEBA Version 2',
        institucion_operante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_contraparte='40072',
        monto=1020,
        nombre_beneficiario='Pablo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='stp_id_again',
        version=2,
    )
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    transaction.estado = Estado.succeeded
    transaction.save()
    # Ejecuta nuevamente la misma orden
    with pytest.raises(ResendSuccessOrderException):
        execute(order)
    transaction.delete()
