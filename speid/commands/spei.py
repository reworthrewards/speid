import click
from mongoengine import DoesNotExist

from speid import app
from speid.models import Transaction
from speid.types import Estado


@app.cli.group('speid')
def speid_group():
    """Perform speid actions."""
    pass


@speid_group.command()
@click.argument('speid_id', type=str)
@click.argument('transaction_status', type=str)
def set_status_transaction(speid_id, transaction_status):
    """Establece el estado de la transacción,
    valores permitidos succeeded y failed"""
    transaction = Transaction.objects.get(speid_id=speid_id)
    if transaction_status == Estado.succeeded.value:
        status = Estado.succeeded
    elif transaction_status == Estado.failed.value:
        status = Estado.failed
    else:
        raise ValueError('Invalid event type')
    transaction.set_status(status)
    transaction.save()


@speid_group.command()
@click.argument('speid_id', type=str)
def re_execute_transactions(speid_id):
    """Encola la transacción para intentar ser enviada
    nuevamente"""
    try:
        transaction = Transaction.objects.get(speid_id=speid_id)
    except DoesNotExist:
        raise ValueError('Transaction not found')

    transaction.create_order()


if __name__ == "__main__":
    ...  # pragma: no cover
