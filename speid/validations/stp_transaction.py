from datetime import datetime
from typing import Optional

from pydantic import BaseModel, StrictStr

from speid.models import Transaction
from speid.models.helpers import base62_uuid, camel_to_snake


class StpTransaction(BaseModel):
    fechaOperacion: int
    institucionOrdenante: str
    institucionBeneficiaria: str
    claveRastreo: StrictStr
    monto: float
    nombreOrdenante: StrictStr
    tipoCuentaOrdenante: int
    cuentaOrdenante: StrictStr
    rfcCurpOrdenante: StrictStr
    nombreBeneficiario: StrictStr
    tipoCuentaBeneficiario: int
    cuentaBeneficiario: StrictStr
    rfcCurpBeneficiario: StrictStr
    conceptoPago: StrictStr
    referenciaNumerica: int
    empresa: StrictStr
    id: Optional[int] = None

    def transform(self) -> Transaction:
        trans_dict = {
            camel_to_snake(k): v
            for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
        trans_dict['stp_id'] = trans_dict.pop('id', None)
        trans_dict['monto'] = round(trans_dict['monto'] * 100)
        transaction = Transaction(**trans_dict)
        transaction.speid_id = base62_uuid('SR')()
        transaction.fecha_operacion = datetime.strptime(
            str(transaction.fecha_operacion), '%Y%m%d'
        ).date()

        return transaction
