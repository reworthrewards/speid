from typing import Any, Dict

from requests import Session

from speid.config import BACKEND_JWT_TOKEN, BACKEND_URL
from speid.exc import BackendError
from speid.types import UpdateOrderType


class BackendClient:
    """
    Based on:
    https://github.com/cuenca-mx/stpmex-python/blob/main/stpmex/client.py
    """

    session: Session

    def __init__(self) -> None:
        self.session = Session()
        self.session.headers = self._auth_header()

    def _auth_header(self) -> dict:
        return dict(Authorization=f'Bearer {BACKEND_JWT_TOKEN}')

    def update_order(self, update_order: UpdateOrderType) -> None:
        data = update_order.dict()
        self._request('POST', 'orden_events', data)

    def receive_order(self, update_order: UpdateOrderType) -> Dict[str, Any]:
        ...

    def _request(
        self, method: str, endpoint: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = BACKEND_URL + endpoint
        response = self.session.request(method, url, json=data)
        if not response.ok:
            raise BackendError(response.text)
        return response.json()
