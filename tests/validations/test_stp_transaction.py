from speid.validations import StpTransaction


def test_converts_float_amount_to_int_correctly() -> None:
    data = dict(
        id=123,
        fechaOperacion=20200320,
        institucionOrdenante='40106',
        institucionBeneficiaria='90646',
        claveRastreo='abc123',
        monto=265.65,
        nombreOrdenante='Frida Kahlo',
        tipoCuentaOrdenante=40,
        cuentaOrdenante='11111',
        rfcCurpOrdenante='ND',
        nombreBeneficiario='Diego Rivera',
        tipoCuentaBeneficiario=40,
        cuentaBeneficiario='99999',
        rfcCurpBeneficiario='ND',
        conceptoPago='AAAA',
        referenciaNumerica=1,
        empresa='baz',
    )
    stp_transaction = StpTransaction(**data)
    transaction = stp_transaction.transform()
    assert transaction.monto == 26565
