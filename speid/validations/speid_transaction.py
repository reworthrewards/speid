from typing import Dict, Optional

from pydantic import BaseModel, StrictStr, validator
from stpmex.types import TipoCuenta

from speid.models import Transaction
from speid.models.helpers import camel_to_snake


class SpeidTransaction(BaseModel):
    concepto_pago: StrictStr
    institucion_operante: StrictStr
    cuenta_beneficiario: StrictStr
    institucion_contraparte: StrictStr
    monto: int
    nombre_beneficiario: StrictStr
    nombre_ordenante: StrictStr
    cuenta_ordenante: StrictStr
    rfc_curp_ordenante: StrictStr
    speid_id: StrictStr
    empresa: Optional[str] = None
    folio_origen: Optional[str] = None
    clave_rastreo: Optional[str] = None
    tipo_pago: int = 1
    tipo_cuenta_ordenante: Optional[str] = None
    rfc_curp_beneficiario: str = "ND"
    email_beneficiario: Optional[str] = None
    tipo_cuenta_beneficiario2: Optional[str] = None
    nombre_beneficiario2: Optional[str] = None
    cuenta_beneficiario2: Optional[str] = None
    rfc_curpBeneficiario2: Optional[str] = None
    concepto_pago2: Optional[str] = None
    clave_cat_usuario1: Optional[str] = None
    clave_cat_usuario2: Optional[str] = None
    clave_pago: Optional[str] = None
    referencia_cobranza: Optional[str] = None
    referencia_numerica: Optional[int] = None
    tipo_operacion: Optional[str] = None
    topologia: str = "T"
    usuario: Optional[str] = None
    medio_entrega: int = 3
    prioridad: int = 1

    def to_dict(self) -> dict:
        return {
            k: v for k, v in self.__dict__.items() if not k.startswith('_')
        }

    @classmethod
    def from_camel_case(cls, values: Dict):
        snake_values = {camel_to_snake(k): v for k, v in values.items()}
        float_amount = float(snake_values['monto'])
        snake_values['monto'] = int(float_amount * 100)
        return cls(**snake_values)

    @property
    def tipo_cuenta_beneficiario(self):
        cuenta_len = len(self.cuenta_beneficiario)
        if cuenta_len == 18:
            return TipoCuenta.clabe.value
        elif cuenta_len in {15, 16}:
            return TipoCuenta.card.value

    @validator('cuenta_beneficiario')
    def validate_cuenta_beneficiario(cls, cuenta_beneficiario):
        cuenta_len = len(cuenta_beneficiario)
        if cuenta_len not in [18, 15, 16]:
            raise ValueError(f'{cuenta_len} is not a valid cuenta length')
        return cuenta_beneficiario

    def transform(self) -> Transaction:
        values = self.to_dict()
        values['institucion_beneficiaria'] = values['institucion_contraparte']
        values['institucion_ordenante'] = values['institucion_operante']
        del values['institucion_contraparte']
        del values['institucion_operante']
        transaction = Transaction(**values)
        return transaction
