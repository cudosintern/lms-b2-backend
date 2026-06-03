from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class UniversityBase(BaseModel):
    unv_id: int
    unv_name: str
    unv_desc: str
    status: Optional[int]
    created_by: int
    modified_by: int
    created_date: date
    modified_date: date
    unv_code: str

    model_config = ConfigDict(from_attributes=True)


class OrganisationTypeBase(BaseModel):
    org_type_id: int
    org_type: str
    org_type_desc: str
    unv_id: int
    status: int

    model_config = ConfigDict(from_attributes=True)


class OrganisationBase(BaseModel):
    org_id: int
    org_name: str
    org_society: Optional[str]
    org_desc: Optional[str]
    unv_id: int
    status: int
    created_by: Optional[int]
    modified_by: Optional[int]
    create_date: Optional[date]
    modify_date: Optional[date]
    org_code: Optional[str]
    org_type_id: Optional[int]
    org_location: Optional[str]
    org_contact_number: Optional[str]
    org_email: Optional[str]
    org_logo: Optional[str]
    profile_image: Optional[str]
    other_profile_image: Optional[str]
    is_medical_flag: int
    certificate_tab_mandatory: int
    bank_tab_mandatory: int
    additional_fee_label: str
    DOB_format: str
    org_address: str
    org_website: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# Response models with relationships
class OrganisationType(OrganisationTypeBase):
    university: Optional[UniversityBase] = None
    organisations: Optional[List[OrganisationBase]] = None


class UniversityResponse(UniversityBase):
    organisation_types: Optional[List[OrganisationTypeBase]] = None
    organisations: Optional[List[OrganisationBase]] = None


class OrganisationResponse(OrganisationBase):
    university: Optional[UniversityBase] = None
    organisation_type: Optional[OrganisationTypeBase] = None