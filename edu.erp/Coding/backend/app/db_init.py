from sqlalchemy import text
from app.core.database import engine

def init_db():
    print("Re-initializing database tables and mentoring mock data...")
    with engine.connect() as conn:
        # Drop tables in reverse dependency order to avoid foreign key issues
        conn.execute(text("DROP TABLE IF EXISTS mentoring_chat_message;"))
        conn.execute(text("DROP TABLE IF EXISTS questionnaire_response;"))
        conn.execute(text("DROP TABLE IF EXISTS questionnaire_question;"))
        conn.execute(text("DROP TABLE IF EXISTS questionnaire;"))
        conn.execute(text("DROP TABLE IF EXISTS mentee_group_map;"))
        conn.execute(text("DROP TABLE IF EXISTS mentoring_session;"))
        conn.execute(text("DROP TABLE IF EXISTS mentoring_group;"))
        conn.execute(text("DROP TABLE IF EXISTS curriculum_mentor_map;"))
        conn.execute(text("DROP TABLE IF EXISTS cross_department_mentor_map;"))
        conn.execute(text("DROP TABLE IF EXISTS iems_users;"))
        conn.execute(text("DROP TABLE IF EXISTS iems_department;"))
        conn.execute(text("DROP TABLE IF EXISTS config_type;"))
        conn.execute(text("DROP TABLE IF EXISTS curriculum;"))
        conn.commit()

        # 1. Create iems_department table
        conn.execute(text("""
            CREATE TABLE iems_department (
                dept_id INT AUTO_INCREMENT PRIMARY KEY,
                dept_name VARCHAR(100) NOT NULL,
                dept_description VARCHAR(500) NULL,
                dept_acronym VARCHAR(20) NULL,
                dept_code_usn VARCHAR(45) NOT NULL,
                status TINYINT(1) DEFAULT 0,
                org_id INT NOT NULL,
                no_batch_dept INT DEFAULT 0,
                dept_hod_id INT NULL,
                created_by INT NULL,
                modified_by INT NULL,
                create_date DATE NULL,
                modify_date DATE NULL
            ) ENGINE=InnoDB;
        """))

        # 2. Create iems_users table
        conn.execute(text("""
            CREATE TABLE iems_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip_address VARBINARY(16) NULL,
                username VARCHAR(40) UNIQUE NULL,
                password VARCHAR(80) NULL,
                salt VARCHAR(40) NULL,
                email VARCHAR(50) UNIQUE NOT NULL,
                activation_code VARCHAR(40) NULL,
                forgotten_password_code VARCHAR(40) NULL,
                forgotten_password_time INT NULL,
                remember_code VARCHAR(40) NULL,
                created_on INT NULL,
                last_login INT NULL,
                failed_login_attempts INT NULL,
                is_locked TINYINT(1) NULL,
                lockout_until DATETIME NULL,
                active INT NULL,
                title VARCHAR(8) NULL,
                first_name VARCHAR(50) NULL,
                middle_name VARCHAR(50) NULL,
                last_name VARCHAR(50) NULL,
                org_id INT NULL,
                user_type VARCHAR(1) NOT NULL,
                user_dept_id INT NULL,
                created_by INT NULL,
                modified_by INT NULL,
                create_date DATE NULL,
                modify_date DATE NULL,
                designation_id INT NULL,
                status INT NOT NULL DEFAULT 1,
                super_admin INT NOT NULL DEFAULT 0,
                technical_admin INT NOT NULL DEFAULT 0,
                student_id INT NULL,
                mobile VARCHAR(10) NULL,
                forgot_password_check TINYINT(1) NULL,
                master_password TEXT NULL,
                alertnative_email VARCHAR(50) NULL,
                organization_name VARCHAR(40) NOT NULL DEFAULT 'IonCUDOS',
                base_dept_id INT NULL,
                user_qualification VARCHAR(50) NULL,
                responsibilities TEXT NULL,
                faculty_mode INT NOT NULL DEFAULT 1,
                indurtrial_experiance INT NOT NULL DEFAULT 0,
                teach_experiance INT NOT NULL DEFAULT 0,
                user_experience FLOAT NULL,
                faculty_type INT NULL,
                phd_from TEXT NULL,
                superviser TEXT NULL,
                phd_status INT NULL DEFAULT 59,
                registration_year DATE NULL,
                phd_topic TEXT NULL,
                phd_status_data TEXT NULL,
                phd_assessment_year DATE NULL,
                user_specialization TEXT NULL,
                guidance_within_org INT NULL,
                guidance_outside_org INT NULL,
                research_interrest TEXT NULL,
                skills TEXT NULL,
                DOB DATE NULL,
                present_address TEXT NULL,
                permanent_address TEXT NULL,
                user_website TEXT NULL,
                emp_no TEXT NULL,
                faculty_serving INT NULL,
                dpdp_flag TINYINT(1) NOT NULL DEFAULT 0,
                is_student TINYINT(1) NOT NULL DEFAULT 0
            ) ENGINE=InnoDB;
        """))

        # 3. Create config_type table
        conn.execute(text("""
            CREATE TABLE config_type (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                status INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
        """))

        # 4. Create cross_department_mentor_map table
        conn.execute(text("""
            CREATE TABLE cross_department_mentor_map (
                id INT AUTO_INCREMENT PRIMARY KEY,
                mentor_id INT NOT NULL,
                mapped_dept_id INT NOT NULL,
                status INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_mentor_dept (mentor_id, mapped_dept_id)
            ) ENGINE=InnoDB;
        """))

        # 5. Create curriculum table
        conn.execute(text("""
            CREATE TABLE curriculum (
                crclm_id INT AUTO_INCREMENT PRIMARY KEY,
                crclm_name VARCHAR(255) NOT NULL,
                status INT DEFAULT 1
            ) ENGINE=InnoDB;
        """))

        # 6. Create curriculum_mentor_map table
        conn.execute(text("""
            CREATE TABLE curriculum_mentor_map (
                id INT AUTO_INCREMENT PRIMARY KEY,
                mentor_id INT NOT NULL,
                curriculum_id INT NOT NULL,
                status INT DEFAULT 1,
                UNIQUE KEY unique_mentor_crclm (mentor_id, curriculum_id)
            ) ENGINE=InnoDB;
        """))

        # 7. Create mentoring_group table
        conn.execute(text("""
            CREATE TABLE mentoring_group (
                id INT AUTO_INCREMENT PRIMARY KEY,
                group_name VARCHAR(255) NOT NULL,
                curriculum_id INT NOT NULL,
                mentor_id INT NOT NULL,
                status INT DEFAULT 1
            ) ENGINE=InnoDB;
        """))

        # 8. Create mentoring_session table
        conn.execute(text("""
            CREATE TABLE mentoring_session (
                id INT AUTO_INCREMENT PRIMARY KEY,
                curriculum_id INT NOT NULL,
                group_id INT NULL,
                mentor_id INT NOT NULL,
                session_date DATE NOT NULL,
                session_time TIME NULL,
                topic VARCHAR(255) NULL,
                description TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
        """))

        # 9. Create mentee_group_map table
        conn.execute(text("""
            CREATE TABLE mentee_group_map (
                id INT AUTO_INCREMENT PRIMARY KEY,
                group_id INT NOT NULL,
                mentee_id INT NOT NULL,
                status INT DEFAULT 1,
                UNIQUE KEY unique_mentee_group (mentee_id, group_id)
            ) ENGINE=InnoDB;
        """))

        # 10. Create questionnaire table
        conn.execute(text("""
            CREATE TABLE questionnaire (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT NULL,
                status INT DEFAULT 1
            ) ENGINE=InnoDB;
        """))

        # 11. Create questionnaire_question table
        conn.execute(text("""
            CREATE TABLE questionnaire_question (
                id INT AUTO_INCREMENT PRIMARY KEY,
                questionnaire_id INT NOT NULL,
                question_text TEXT NOT NULL,
                field_type VARCHAR(50) NOT NULL,
                field_settings TEXT NULL,
                status INT DEFAULT 1
            ) ENGINE=InnoDB;
        """))

        # 12. Create questionnaire_response table
        conn.execute(text("""
            CREATE TABLE questionnaire_response (
                id INT AUTO_INCREMENT PRIMARY KEY,
                questionnaire_id INT NOT NULL,
                mentee_id INT NOT NULL,
                question_id INT NOT NULL,
                response_value TEXT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
        """))

        # 13. Create mentoring_chat_message table
        conn.execute(text("""
            CREATE TABLE mentoring_chat_message (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                receiver_id INT NULL,
                group_id INT NULL,
                message_text TEXT NOT NULL,
                is_general TINYINT(1) DEFAULT 0,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
        """))

        # ---------------- POPULATE MOCK DATA ----------------
        
        # Mock departments
        conn.execute(text("""
            INSERT INTO iems_department (dept_id, dept_name, dept_acronym, dept_code_usn, org_id, status) VALUES
            (1, 'Computer Science & Engineering', 'CSE', 'USN01', 1, 1),
            (2, 'Information Science & Engineering', 'ISE', 'USN02', 1, 1),
            (3, 'Electronics & Communication', 'ECE', 'USN03', 1, 1)
        """))

        # Mock users
        conn.execute(text("""
            INSERT INTO iems_users (id, username, email, first_name, last_name, user_dept_id, org_id, user_type, active, status) VALUES
            (1, 'test', 'test@lms.com', 'Coe', 'Staff', 1, 1, 'U', 1, 1),
            (2, 'mentor_cse', 'cse@lms.com', 'Rajesh', 'Kumar', 1, 1, 'U', 1, 1),
            (3, 'mentor_ise', 'ise@lms.com', 'Anita', 'Sharma', 2, 1, 'U', 1, 1),
            (4, 'mentor_ece', 'ece@lms.com', 'Suresh', 'Raina', 3, 1, 'U', 1, 1),
            (5, 'student_a', 'studenta@lms.com', 'Amit', 'Patel', 1, 1, 'S', 1, 1),
            (6, 'student_b', 'studentb@lms.com', 'Bhavesh', 'Shah', 1, 1, 'S', 1, 1)
        """))

        # Mock curriculum
        conn.execute(text("""
            INSERT INTO curriculum (crclm_id, crclm_name, status) VALUES
            (1, 'CSE 2026 Batch Curriculum', 1),
            (2, 'ISE 2026 Batch Curriculum', 1)
        """))

        # Mock curriculum mentor map
        conn.execute(text("""
            INSERT INTO curriculum_mentor_map (id, mentor_id, curriculum_id, status) VALUES
            (1, 1, 1, 1),
            (2, 1, 2, 1)
        """))

        # Mock mentoring groups
        conn.execute(text("""
            INSERT INTO mentoring_group (id, group_name, curriculum_id, mentor_id, status) VALUES
            (1, 'CSE Mentoring Group Alpha', 1, 1, 1),
            (2, 'ISE Mentoring Group Beta', 2, 1, 1)
        """))

        # Mock mentoring sessions
        conn.execute(text("""
            INSERT INTO mentoring_session (id, curriculum_id, group_id, mentor_id, session_date, session_time, topic, description) VALUES
            (1, 1, 1, 1, '2026-06-10', '10:00:00', 'Career Counseling', 'Discussing job search strategy and skill set mapping.'),
            (2, 1, 1, 1, '2026-06-25', '14:30:00', 'Academic Progress Review', 'Reviewing student test marks and class doubts.')
        """))

        # Mock mentee mapping
        conn.execute(text("""
            INSERT INTO mentee_group_map (id, group_id, mentee_id, status) VALUES
            (1, 1, 5, 1),
            (2, 1, 6, 1)
        """))

        # Mock questionnaire
        conn.execute(text("""
            INSERT INTO questionnaire (id, title, description, status) VALUES
            (1, 'Monthly Mentee Questionnaire', 'Please rate your monthly learning and mention any issues.', 1)
        """))

        # Mock questionnaire questions
        conn.execute(text("""
            INSERT INTO questionnaire_question (id, questionnaire_id, question_text, field_type, field_settings, status) VALUES
            (1, 1, 'Rate your learning progress', 'select', '{"required": true, "options": ["Excellent", "Good", "Average", "Below Average"]}', 1),
            (2, 1, 'Describe any issues faced this month', 'text', '{"required": false, "placeholder": "Enter details here..."}', 1)
        """))

        # Mock responses
        conn.execute(text("""
            INSERT INTO questionnaire_response (id, questionnaire_id, mentee_id, question_id, response_value) VALUES
            (1, 1, 5, 1, 'Good'),
            (2, 1, 5, 2, 'Need extra support in Database Management Systems course.'),
            (3, 1, 6, 1, 'Excellent'),
            (4, 1, 6, 2, 'All going well!')
        """))

        # Mock chat messages
        conn.execute(text("""
            INSERT INTO mentoring_chat_message (id, sender_id, receiver_id, group_id, message_text, is_general) VALUES
            (1, 5, 1, NULL, 'Hello sir, when is our next mentoring session?', 0),
            (2, 1, 5, NULL, 'It is scheduled for next Monday at 10 AM.', 0),
            (3, 1, NULL, 1, 'Announcement: Please submit your monthly questionnaire by tomorrow evening.', 1)
        """))

        conn.commit()
    print("Database initialization complete!")

if __name__ == "__main__":
    init_db()
