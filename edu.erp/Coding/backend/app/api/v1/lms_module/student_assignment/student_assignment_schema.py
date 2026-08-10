from pydantic import BaseModel
#classes
class AssignmentListRequest(BaseModel):
    course_id: int
    semester_id: int
    academic_batch_id: int

class StudentAssignmentReportRequest(BaseModel):
    assignment_id: int