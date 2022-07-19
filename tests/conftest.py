import datetime as dt
from typing import Generator
from unittest.mock import patch

import pytest

from speid.models import Transaction


@pytest.fixture
def mock_backend():
    with patch('requests.Session.request') as requestMock:
        requestMock.return_value.json.return_value = dict(mocked=True)
        requestMock.return_value.ok = True
        yield


@pytest.fixture(scope='module')
def vcr_config():
    config = dict()
    config['record_mode'] = 'none'
    return config


@pytest.fixture
def outcome_transaction() -> Generator[Transaction, None, None]:
    transaction = Transaction(
        stp_id=2456305,
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
        empresa='someEmpresa',
    )
    transaction.save()
    yield transaction
    transaction.delete()


@pytest.fixture
def orden_pago(outcome_transaction):
    return dict(
        ordenPago=dict(
            clavePago='',
            claveRastreo='CUENCA871574313626',
            conceptoPago='Dinerito',
            conceptoPago2='',
            cuentaBeneficiario='012180015025335996',
            cuentaBeneficiario2='',
            cuentaOrdenante=outcome_transaction.cuenta_ordenante,
            empresa='TAMIZI',
            estado='LQ',
            fechaOperacion='20220407',
            folioOrigen='CUENCA871574313626',
            horaServidorBanxico='18:19:25',
            idCliente='CUENCA871574313626',
            idEF=223722378,
            institucionContraparte=40012,
            institucionOperante=90646,
            medioEntrega=3,
            monto=10.0,
            nombreBeneficiario='Alex',
            nombreBeneficiario2='',
            nombreCEP='',
            nombreOrdenante=outcome_transaction.nombre_ordenante,
            prioridad=1,
            referenciaCobranza='',
            referenciaNumerica=4346435,
            rfcCEP='',
            rfcCurpBeneficiario='AAAA951020BBB',
            rfcCurpBeneficiario2='',
            rfcCurpOrdenante='AAAA951020HMCRQN00',
            sello='',
            tipoCuentaBeneficiario=40,
            tipoCuentaOrdenante=40,
            tipoPago=1,
            topologia='V',
            tsEntrega=9.155,
            urlCEP='https://www.banxico.org.mx/cep/go?i=90646',
            usuario='foo',
        )
    )
