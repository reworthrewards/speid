from datetime import datetime

from mongoengine import (
    DateTimeField,
    Document,
    EnumField,
    IntField,
    StringField,
    signals,
)
from stpmex.resources import Orden

from speid.config import STP_EMPRESA
from speid.processors import stpmex_client
from speid.types import Estado

from .events import Event
from .helpers import date_now, delete_events, handler, save_events, updated_at


@handler(signals.pre_save)
def pre_save_transaction(sender, document):
    date = document.fecha_operacion or datetime.today()
    document.compound_key = (
        f'{document.clave_rastreo}:{date.strftime("%Y%m%d")}'
    )


@updated_at.apply
@save_events.apply
@pre_save_transaction.apply
@delete_events.apply
class Transaction(Document):
    created_at = date_now()
    updated_at = DateTimeField()
    stp_id = IntField()
    fecha_operacion = DateTimeField()
    institucion_ordenante = StringField()
    institucion_beneficiaria = StringField()
    clave_rastreo = StringField()
    monto = IntField()
    nombre_ordenante = StringField()
    tipo_cuenta_ordenante = IntField()
    cuenta_ordenante = StringField()
    rfc_curp_ordenante = StringField()
    nombre_beneficiario = StringField()
    tipo_cuenta_beneficiario = IntField()
    cuenta_beneficiario = StringField()
    rfc_curp_beneficiario = StringField()
    concepto_pago = StringField()
    referencia_numerica = IntField()
    empresa = StringField()
    estado = EnumField(Estado, default=Estado.created)
    speid_id = StringField()
    folio_origen = StringField()
    tipo_pago = IntField()
    email_beneficiario = StringField()
    tipo_cuenta_beneficiario2 = StringField()
    nombre_beneficiario2 = StringField()
    cuenta_beneficiario2 = StringField()
    rfc_curpBeneficiario2 = StringField()
    concepto_pago2 = StringField()
    clave_cat_usuario1 = StringField()
    clave_cat_usuario2 = StringField()
    clave_pago = StringField()
    referencia_cobranza = StringField()
    tipo_operacion = StringField()
    topologia = StringField()
    usuario = StringField()
    medio_entrega = IntField()
    prioridad = IntField()
    compound_key = StringField()
    detalle = StringField()

    curp_ordenante = StringField()
    rfc_ordenante = StringField()

    meta = {
        'indexes': [
            '+stp_id',
            '+speid_id',
            '+clave_rastreo',
            # The Unique-Sparse index skips over any document that is missing
            # the indexed field (null values)
            {'fields': ['+compound_key'], 'unique': True, 'sparse': True},
        ]
    }

    def set_status(self, status: Estado):
        self.estado = status

    def create_order(self) -> Orden:
        # Don't send if stp_id already exists
        if self.stp_id:
            return Orden(  # type: ignore
                id=self.stp_id,
                monto=self.monto / 100.0,
                conceptoPago=self.concepto_pago,
                nombreBeneficiario=self.nombre_beneficiario,
                cuentaBeneficiario=self.cuenta_beneficiario,
                institucionContraparte=self.institucion_beneficiaria,
                cuentaOrdenante=self.cuenta_ordenante,
            )

        optionals = dict(
            institucionOperante=self.institucion_ordenante,
            claveRastreo=self.clave_rastreo,
            referenciaNumerica=self.referencia_numerica,
            rfcCurpBeneficiario=self.rfc_curp_beneficiario,
            medioEntrega=self.medio_entrega,
            prioridad=self.prioridad,
            tipoPago=self.tipo_pago,
            topologia=self.topologia,
        )
        # remove if value is None
        remove = []
        for k, v in optionals.items():
            if v is None:
                remove.append(k)
        for k in remove:
            optionals.pop(k)

        try:
            order = stpmex_client.ordenes.registra(
                monto=self.monto / 100.0,
                conceptoPago=self.concepto_pago,
                nombreBeneficiario=self.nombre_beneficiario,
                cuentaBeneficiario=self.cuenta_beneficiario,
                institucionContraparte=self.institucion_beneficiaria,
                tipoCuentaBeneficiario=self.tipo_cuenta_beneficiario,
                nombreOrdenante=self.nombre_ordenante,
                cuentaOrdenante=self.cuenta_ordenante,
                rfcCurpOrdenante=self.rfc_curp_ordenante,
                **optionals,
            )
        except (Exception) as e:  # Anything can happen here
            self.save()
            Event(target_document_id=str(self.id), metadata=str(e)).save()
            raise e
        else:
            self.clave_rastreo = self.clave_rastreo or order.claveRastreo
            self.rfc_curp_beneficiario = (
                self.rfc_curp_beneficiario or order.rfcCurpBeneficiario
            )
            self.referencia_numerica = (
                self.referencia_numerica or order.referenciaNumerica
            )
            self.empresa = self.empresa or STP_EMPRESA
            self.stp_id = order.id

            self.estado = Estado.submitted
            self.save()
            return order
