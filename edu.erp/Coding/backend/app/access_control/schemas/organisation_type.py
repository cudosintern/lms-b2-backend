from pydantic import BaseModel


class OrganisationTypeData(BaseModel):
    org_type_id: int
    org_type: str
    org_type_desc: str
    unv_id: int
    status: int
