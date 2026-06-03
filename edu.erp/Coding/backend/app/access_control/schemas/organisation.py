from pydantic import BaseModel


class OrganisationData(BaseModel):
    org_id: int
    org_name: str
    org_society: str
    org_desc: str
    unv_id: int
    status: int
    created_by: int
    modified_by: int
    create_date: str
    modify_date: str
    org_code: str
    org_type_id: int
    profile_image: str
    other_profile_image: str
