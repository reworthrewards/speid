from stpmex import Client
from typing import Optional
from requests import Session
from stpmex.version import __version__ as client_version
from stpmex.client import DEMO_HOST, PROD_HOST
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from stpmex.resources import Resource
from stpmex.exc import InvalidPassphrase


class StpClient(Client):
    def __init__(self, empresa: str, priv_key: str, priv_key_passphrase: Optional[str], demo: bool = False, base_url: str = None, soap_url: str = None, timeout: tuple = None):
        self.timeout = timeout
        self.session = Session()
        self.session.headers['User-Agent'] = f'stpmex-python/{client_version}'
        if demo:
            host_url = DEMO_HOST
            self.session.verify = False
        else:
            host_url = PROD_HOST
            self.session.verify = True
        self.base_url = base_url or f'{host_url}/speiws/rest'
        self.soap_url = (
            soap_url or f'{host_url}/spei/webservices/SpeiConsultaServices'
        )

        try:
            self.pkey = serialization.load_pem_private_key(
                priv_key.encode('utf-8'),
                priv_key_passphrase.encode('ascii') if priv_key_passphrase else None,
                default_backend(),
            )
        except (ValueError, TypeError, UnsupportedAlgorithm):
            raise InvalidPassphrase
        Resource.empresa = empresa
        Resource._client = self
