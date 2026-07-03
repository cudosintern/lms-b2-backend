from pydantic import BaseModel


class StudentAgreeSchema(BaseModel):
    lms_isnob_id: int