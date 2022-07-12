from pydantic import BaseModel

from speid.types import Estado


class UpdateSpeidTransaction(BaseModel):
    speid_id: str
    orden_id: str
    estado: Estado
