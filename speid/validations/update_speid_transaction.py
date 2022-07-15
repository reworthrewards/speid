from pydantic import BaseModel

from speid.types import Estado


class UpdateSpeidTransaction(BaseModel):
    id: str
    empresa: str
    estado: Estado
