import pytest

from speid import app


@pytest.fixture
def client():
    app.testing = True
    client = app.test_client()
    return client


@pytest.fixture
def default_blocked_transaction():
    return dict(
        id=2456304,
        fechaOperacion=20180618,
        institucionOrdenante=40012,
        institucionBeneficiaria=90646,
        claveRastreo="PRUEBABloqueo",
        monto=100.0,
        nombreOrdenante="BANCO",
        tipoCuentaOrdenante=40,
        cuentaOrdenante="846180000500000009",
        rfcCurpOrdenante="ND",
        nombreBeneficiario="TAMIZI",
        tipoCuentaBeneficiario=40,
        cuentaBeneficiario="646180157000000666",
        rfcCurpBeneficiario="ND",
        conceptoPago="PRUEBA BLOQUEO",
        referenciaNumerica=2423,
        empresa="TAMIZI",
    )


@pytest.fixture
def default_blocked_incoming_transaction():
    return dict(
        id=24569304,
        fechaOperacion=20180618,
        institucionOrdenante=40012,
        institucionBeneficiaria=90646,
        claveRastreo="PRUEBABloqueo",
        monto=100.0,
        nombreOrdenante="BANCO",
        tipoCuentaOrdenante=40,
        cuentaOrdenante="846180000500000109",
        rfcCurpOrdenante="ND",
        nombreBeneficiario="TAMIZI",
        tipoCuentaBeneficiario=40,
        cuentaBeneficiario="646180157000000667",
        rfcCurpBeneficiario="ND",
        conceptoPago="PRUEBA BLOQUEO",
        referenciaNumerica=2423,
        empresa="TAMIZI",
    )


@pytest.fixture
def default_income_transaction():
    return dict(
        abono=dict(
            id=2456303,
            fechaOperacion=20180618,
            institucionOrdenante=40012,
            institucionBeneficiaria=90646,
            claveRastreo="PRUEBATAMIZI1",
            monto=100.0,
            nombreOrdenante="BANCO",
            tipoCuentaOrdenante=40,
            cuentaOrdenante="846180000500000008",
            rfcCurpOrdenante="ND",
            nombreBeneficiario="TAMIZI",
            tipoCuentaBeneficiario=40,
            cuentaBeneficiario="646180157000000004",
            rfcCurpBeneficiario="ND",
            conceptoPago="PRUEBA",
            referenciaNumerica=2423,
            empresa="TAMIZI",
        )
    )
