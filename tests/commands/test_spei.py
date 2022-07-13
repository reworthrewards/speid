import pytest
from click.testing import CliRunner

from speid.commands.spei import speid_group
from speid.models import Transaction
from speid.types import Estado


@pytest.fixture
def transaction():
    transaction = Transaction(
        concepto_pago='PRUEBA',
        institucion_ordenante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='40072',
        monto=1020,
        nombre_beneficiario='Ricardo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='speid_id',
    )
    transaction.save()

    yield transaction

    transaction.delete()


def test_set_status_transaction(mock_backend, transaction):
    id_trx = transaction.id
    assert transaction.estado is Estado.created

    runner = CliRunner()
    runner.invoke(
        speid_group,
        ['set-status-transaction', str(transaction.speid_id), 'succeeded'],
    )

    transaction = Transaction.objects.get(id=id_trx)
    assert transaction.estado is Estado.succeeded


def test_set_status_failed_transaction(mock_backend, transaction):
    id_trx = transaction.id
    assert transaction.estado is Estado.created

    runner = CliRunner()
    runner.invoke(
        speid_group,
        ['set-status-transaction', str(transaction.speid_id), 'failed'],
    )

    transaction = Transaction.objects.get(id=id_trx)
    assert transaction.estado is Estado.failed


def test_set_status_invalid_transaction(mock_backend, transaction):
    id_trx = transaction.id
    assert transaction.estado is Estado.created

    runner = CliRunner()
    result = runner.invoke(
        speid_group,
        ['set-status-transaction', str(transaction.speid_id), 'invalid'],
    )

    transaction = Transaction.objects.get(id=id_trx)
    assert transaction.estado is Estado.created
    assert type(result.exception) is ValueError


@pytest.mark.vcr
def test_re_execute_transactions(runner, transaction):
    id_trx = transaction.id
    assert transaction.estado is Estado.created

    runner = CliRunner()
    runner.invoke(
        speid_group, ['re-execute-transactions', transaction.speid_id]
    )

    transaction = Transaction.objects.get(id=id_trx)

    assert transaction.estado is Estado.submitted


def test_re_execute_transaction_not_found(runner, transaction):
    id_trx = transaction.id
    assert transaction.estado is Estado.created

    runner = CliRunner()
    result = runner.invoke(
        speid_group, ['re-execute-transactions', 'invalid_speid_id']
    )

    transaction = Transaction.objects.get(id=id_trx)

    assert transaction.estado is Estado.created
    assert type(result.exception) is ValueError
