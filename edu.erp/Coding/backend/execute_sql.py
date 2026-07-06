from app.core.database import engine
from sqlalchemy import text

sql = """
CREATE TABLE IF NOT EXISTS lms_cross_dept_users_crclms (
  id int(11) NOT NULL AUTO_INCREMENT,
  cross_dept_id INT(10) UNSIGNED NOT NULL,
  dept_id INT(10) UNSIGNED DEFAULT NULL,
  faculty_user_id INT(10) UNSIGNED DEFAULT NULL,
  academic_batch_id INT(10) UNSIGNED DEFAULT NULL,
  created_by INT(10) UNSIGNED DEFAULT NULL,
  modified_by INT(10) UNSIGNED DEFAULT NULL,
  created_date datetime DEFAULT CURRENT_TIMESTAMP,
  modified_date datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),

  KEY cross_dept_id (cross_dept_id),
  KEY dept_id (dept_id),
  KEY faculty_user_id (faculty_user_id),
  KEY academic_batch_id (academic_batch_id),

  CONSTRAINT fk_cross_dept
    FOREIGN KEY (cross_dept_id)
    REFERENCES lms_cross_dept_users (cross_dept_id)
    ON DELETE CASCADE ON UPDATE CASCADE,

  CONSTRAINT fk_dept
    FOREIGN KEY (dept_id)
    REFERENCES iems_department (dept_id)
    ON DELETE CASCADE ON UPDATE CASCADE,

  CONSTRAINT fk_user
    FOREIGN KEY (faculty_user_id)
    REFERENCES iems_users (id)
    ON DELETE CASCADE ON UPDATE CASCADE,

  CONSTRAINT fk_batch
    FOREIGN KEY (academic_batch_id)
    REFERENCES iems_academic_batch (academic_batch_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
"""

print("Executing SQL to create lms_cross_dept_users_crclms...")
with engine.connect() as conn:
    conn.execute(text(sql))
    conn.commit()
print("Table created successfully!")
