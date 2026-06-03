import sqlite3
import os
from app.utils.logger import get_logger

logger = get_logger("database")

def init_database(db_path: str = "data.db"):
    logger.info(f"Checking/Initializing SQLite database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        manager_name TEXT,
        building TEXT
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        department_id INTEGER,
        enroll_date TEXT,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        credits INTEGER,
        department_id INTEGER,
        is_online INTEGER DEFAULT 0,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        student_id INTEGER,
        course_id INTEGER,
        grade TEXT,
        enroll_semester TEXT,
        PRIMARY KEY (student_id, course_id),
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (course_id) REFERENCES courses(id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS professors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        office TEXT,
        department_id INTEGER,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classrooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        building TEXT NOT NULL,
        room_number TEXT NOT NULL,
        capacity INTEGER
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS salaries (
        employee_id INTEGER,
        amount INTEGER NOT NULL,
        year INTEGER NOT NULL,
        PRIMARY KEY (employee_id, year)
    );
    """)
    
    cursor.execute("SELECT COUNT(*) FROM departments;")
    if cursor.fetchone()[0] == 0:
        logger.info("Database is empty. Seeding mock college data...")
        
        depts = [
            (1, "Computer Science", "Dr. Sarah Connor", "Main Hall"),
            (2, "Mathematics", "Dr. Alan Turing", "Main Hall"),
            (3, "Biology", "Dr. Richard Dawkins", "Science Center"),
            (4, "History", "Dr. Howard Zinn", "Arts Building")
        ]
        cursor.executemany("INSERT INTO departments VALUES (?,?,?,?)", depts)
        
        studs = [
            (1, "Alice Smith", "alice@university.edu", 1, "2023-09-01"),
            (2, "Bob Jones", "bob@university.edu", 1, "2023-09-01"),
            (3, "Charlie Brown", "charlie@university.edu", 2, "2023-10-15"),
            (4, "Diana Prince", "diana@university.edu", 3, "2024-01-10"),
            (5, "Evan Wright", "evan@university.edu", 4, "2024-02-15"),
            (6, "Fiona Gallagher", "fiona@university.edu", 1, "2023-09-01"),
            (7, "George Costanza", "george@university.edu", 2, "2023-09-01"),
            (8, "Hannah Abbott", "hannah@university.edu", 3, "2024-01-10"),
            (9, "Ian Malcolm", "ian@university.edu", 3, "2023-09-01"),
            (10, "Julia Roberts", "julia@university.edu", 4, "2023-09-01")
        ]
        cursor.executemany("INSERT INTO students VALUES (?,?,?,?,?)", studs)
        
        crss = [
            (1, "Introduction to Python", 3, 1, 1),
            (2, "Database Management Systems", 4, 1, 0),
            (3, "Calculus I", 4, 2, 0),
            (4, "Linear Algebra", 3, 2, 0),
            (5, "Genetics and Evolution", 3, 3, 0),
            (6, "World History 101", 3, 4, 0)
        ]
        cursor.executemany("INSERT INTO courses VALUES (?,?,?,?,?)", crss)
        
        enr = [
            (1, 1, "A", "Fall 2023"),
            (1, 2, "B", "Fall 2023"),
            (2, 1, "B", "Fall 2023"),
            (3, 3, "C", "Fall 2023"),
            (3, 4, "A", "Spring 2024"),
            (4, 5, "A", "Spring 2024"),
            (5, 6, "B", "Spring 2024"),
            (6, 1, "C", "Fall 2023"),
            (6, 2, "F", "Fall 2023"),
            (7, 3, "D", "Fall 2023"),
            (8, 5, "B", "Spring 2024"),
            (9, 5, "A", "Fall 2023"),
            (10, 6, "A", "Fall 2023")
        ]
        cursor.executemany("INSERT INTO enrollments VALUES (?,?,?,?)", enr)
        
        profs = [
            (1, "Dr. Sarah Connor", "sconnor@university.edu", "Room 302", 1),
            (2, "Dr. Alan Turing", "aturing@university.edu", "Room 105", 2),
            (3, "Dr. Richard Dawkins", "rdawkins@university.edu", "Room 401", 3),
            (4, "Dr. Howard Zinn", "hzinn@university.edu", "Room 204", 4)
        ]
        cursor.executemany("INSERT INTO professors VALUES (?,?,?,?,?)", profs)
        
        clss = [
            (1, "Main Hall", "101A", 120),
            (2, "Main Hall", "204", 45),
            (3, "Science Center", "302", 60),
            (4, "Science Center", "105", 30)
        ]
        cursor.executemany("INSERT INTO classrooms VALUES (?,?,?,?)", clss)
        
        sals = [
            (1, 120000, 2023),
            (2, 135000, 2023),
            (3, 110000, 2023),
            (4, 95000, 2023),
            (1, 125000, 2024),
            (2, 140000, 2024),
            (3, 115000, 2024),
            (4, 98000, 2024)
        ]
        cursor.executemany("INSERT INTO salaries VALUES (?,?,?)", sals)
        
        conn.commit()
        logger.info("Mock college data seeded successfully!")
        
    conn.close()

def run_sql(sql: str, db_path: str = "data.db") -> dict:
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        cursor.execute(sql)
        
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        rows = cursor.fetchall()
        
        serialized_rows = [list(row) for row in rows]
        
        return {
            "columns": columns,
            "rows": serialized_rows,
            "row_count": len(serialized_rows),
            "error": None
        }
    except Exception as e:
        logger.error(f"SQL execution error for query '{sql}': {str(e)}")
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "error": str(e)
        }
    finally:
        if conn:
            conn.close()
