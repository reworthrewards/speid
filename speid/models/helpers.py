import re
from datetime import datetime
from typing import Callable

from blinker.base import NamedSignal
from mongoengine import (
    DateTimeField,
    signals,
)
from speid.models import Event

_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
_underscorer2 = re.compile('([a-z0-9])([A-Z])')


def camel_to_snake(s: str) -> str:
    """
    https://gist.github.com/jaytaylor/3660565
    """
    subbed = _underscorer1.sub(r'\1_\2', s)
    return _underscorer2.sub(r'\1_\2', subbed).lower()


def handler(event: NamedSignal):
    """
    http://docs.mongoengine.org/guide/signals.html?highlight=update
    Signal decorator to allow use of callback functions as class
    decorators
    """

    def decorator(fn: Callable):
        def apply(cls):
            event.connect(fn, sender=cls)
            return cls

        fn.apply = apply  # type: ignore
        return fn

    return decorator


def date_now() -> DateTimeField:
    return DateTimeField(default=datetime.utcnow)


@handler(signals.pre_save)
def updated_at(_, document):
    document.updated_at = datetime.utcnow()


@handler(signals.pre_save)
def save_events(_, document):
    Event(target_document_id=document.id, metadata=str(document)).save()


@handler(signals.pre_delete)
def delete_events(_, document):
    Event(target_document_id=document.id, metadata=str(document)).save()
