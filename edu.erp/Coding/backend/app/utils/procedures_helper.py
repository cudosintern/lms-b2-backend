from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..db.models import IEMOrganisation, IEMSAcademicBatch, IEMSDepartment, IEMStudents, IEMUniversity
#procedure calling
# def admission_gen_new_regno(db: Session, department_id: int, academic_batch_id: int, org_id: int):
#     try:
#         # Get the raw connection from SQLAlchemy session
#         connection = db.connection().connection  # Get the raw connection from SQLAlchemy
#         print("Raw connection acquired.")

#         # Prepare a cursor and call the stored procedure
#         with connection.cursor() as cursor:
#             print("Cursor created, calling stored procedure 'getregno'.")

#             # Call the procedure with parameters
#             cursor.callproc('getregno', [department_id, academic_batch_id, org_id])
#             print(f"Stored procedure called with params: department_id={department_id}, academic_batch_id={academic_batch_id}, org_id={org_id}")

#             # MySQL may have multiple result sets, advance to the final one
#             while cursor.nextset():
#                 print("Advancing to the next result set (if any).")

#             # Fetch the actual registration number result
#             result = cursor.fetchone()
#             print("Fetched result:", result)

#             connection.commit()  # Commit to finalize and clear the connection state
#             print("Connection committed successfully.")

#         # Return the registration number if found, otherwise return None
#         if result and result[0]:
#             print("Registration number retrieved successfully:", result[0])
#             return result[0]  # Assuming the registration number is in the first column
#         else:
#             print("No registration number found in the result.")
#             return None

#     except Exception as e:
#         db.rollback()  # Rollback in case of error
#         print("Error encountered, rolling back:", str(e))
#         return None

#     except Exception as e:
#         db.rollback()  # Rollback in case of error
#         print("Error encountered, rolling back:", str(e))
#         # raise HTTPException(status_code=500, detail=f"Error generating registration number: {str(e)}")
#         return None


    
    
def admission_gen_new_regno(db: Session, department_id: int, academic_batch_id: int, org_id: int):
    try:
        # Retrieve university code
        result = db.execute(
            select(IEMUniversity.unv_code)
            .join(IEMOrganisation, IEMOrganisation.unv_id == IEMUniversity.unv_id)
            .where(IEMOrganisation.org_id == org_id)
        )
        unvcode = result.scalar_one_or_none()

        # Retrieve organization code
        result = db.execute(
            select(IEMOrganisation.org_code)
            .where(IEMOrganisation.org_id == org_id)
        )
        orgcode = result.scalar_one_or_none()

        # Retrieve academic year suffix
        result = db.execute(
            select(func.substr(IEMSAcademicBatch.academic_year, 3, 2))
            .where(IEMSAcademicBatch.academic_batch_id == academic_batch_id)
        )
        acayear = result.scalar_one_or_none()

        # Retrieve department acronym
        result = db.execute(
            select(IEMSDepartment.dept_acronym)
            .where(IEMSDepartment.dept_id == department_id)
        )
        dept = result.scalar_one_or_none()

        # Construct the unique registration code
        unvorg_code = f"{unvcode}{orgcode}{acayear}{dept}"

        # Find the highest existing serial number
        result = db.execute(
            select(func.max(func.right(IEMStudents.regno, 4)))
            .where(IEMStudents.regno.like(f"{unvorg_code}%"))
        )
        serialno = result.scalar_one_or_none()

        # Determine the next serial number
        newserialno = (int(serialno) + 1) if serialno else 1

        # Construct the registration number
        reg_no = f"{unvcode}{orgcode}{acayear}{dept}{str(newserialno).zfill(4)}"

        return reg_no

    except Exception as e:
        print(f"Error: {e}")
        return None