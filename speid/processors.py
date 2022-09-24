from speid.backend_client import BackendClient
from speid.config import (
    SPEID_ENV,
    STP_BASE_URL,
    STP_EMPRESA,
    STP_KEY_PASSPHRASE,
    STP_PRIVATE_KEY,
)
from speid.stp_client import StpClient

stpmex_client = StpClient(
    empresa=STP_EMPRESA,
    priv_key=STP_PRIVATE_KEY,
    priv_key_passphrase=STP_KEY_PASSPHRASE,
    demo=SPEID_ENV != 'prod',
    base_url=STP_BASE_URL,
)

# Cliente para el backend
backend_client = BackendClient()
