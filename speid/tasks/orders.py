import clabe
import luhnmod10
from mongoengine import DoesNotExist
from sentry_sdk import capture_exception

from speid.exc import MalformedOrderException, ResendSuccessOrderException
from speid.models import Transaction
from speid.tasks import celery
from speid.types import Estado
from speid.validations import SpeidTransaction


def retry_timeout(attempts: int) -> int:
    # Los primeros 30 segundos lo intenta 5 veces
    if attempts <= 5:
        return 2 * attempts

    # Después lo intenta cada 20 minutos
    return 1200


@celery.task(bind=True, max_retries=12)
def send_order(self, order_values: dict):
    try:
        execute(order_values)
    except (MalformedOrderException, ResendSuccessOrderException) as exc:
        capture_exception(exc)
    except Exception as exc:
        capture_exception(exc)
        self.retry(countdown=retry_timeout(self.request.retries))


def execute(order_values: dict):
    transaction = Transaction()
    try:
        speid_transaction = SpeidTransaction.from_camel_case(order_values)
        transaction = speid_transaction.transform()

        if not clabe.validate_clabe(transaction.cuenta_beneficiario) and (
            not luhnmod10.valid(transaction.cuenta_beneficiario)
        ):
            raise MalformedOrderException()
    except (MalformedOrderException, TypeError, ValueError):
        transaction.set_status(Estado.error)
        transaction.save()
        raise MalformedOrderException()

    try:
        prev_trx = Transaction.objects.get(speid_id=transaction.speid_id)
        # Si la transacción ya esta como succeeded termina
        # Puede suceder cuando se corre la misma tarea tiempo después
        # Y la transacción ya fue confirmada por stp
        assert prev_trx.estado != Estado.succeeded
        transaction = prev_trx
    except DoesNotExist:
        transaction.save()
        pass
    except AssertionError:
        # Para evitar que se vuelva a mandar o regresar se manda la excepción
        raise ResendSuccessOrderException()

    transaction.create_order()
