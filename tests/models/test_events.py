from speid.models import Event, Transaction
from speid.types import EventType


def test_event():
    transaction = Transaction()
    transaction.save()
    id_trx = transaction.id
    transaction.delete()

    events = Event.objects(target_document_id=str(id_trx))
    assert len(events) == 2
    assert 'Created: ' in events[0].metadata
    assert 'Deleted: ' in events[1].metadata
