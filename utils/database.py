import os
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.db_path = os.getenv('DATABASE_PATH', 'teaching_assistant.db')
        self.files_dir = Path('uploaded_files')
        self.files_dir.mkdir(exist_ok=True)
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Establish SQLite connection and create tables"""
        try:
            # Connect to SQLite database
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            print(f"✅ Connected to SQLite database: {self.db_path}")
            
            self._create_tables()
            self._setup_default_settings()
            self._setup_default_users()
            self.connected = True
            
        except Exception as e:
            print(f"❌ Failed to connect to SQLite database: {e}")
            raise
    
    def _create_tables(self):
        """Create SQLite tables if they don't exist"""
        try:
            cursor = self.conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'student',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    total_marks INTEGER DEFAULT 0,
                    date TEXT,
                    duration INTEGER DEFAULT 60,
                    questions TEXT,  -- JSON string
                    rubric_file_id TEXT,  -- ID of uploaded rubric file
                    rubric_data TEXT,  -- JSON string of parsed rubric table
                    rubric_extracted BOOLEAN DEFAULT 0,  -- Whether rubric has been processed
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Submissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id TEXT UNIQUE NOT NULL,
                    test_id TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    answers TEXT,  -- JSON string
                    score INTEGER DEFAULT 0,
                    max_score INTEGER DEFAULT 0,
                    feedback TEXT,  -- JSON string
                    status TEXT DEFAULT 'submitted',
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    graded_at TIMESTAMP,
                    FOREIGN KEY (test_id) REFERENCES tests(test_id),
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    UNIQUE(test_id, student_id)
                )
            ''')
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_type TEXT UNIQUE NOT NULL,
                    prompt_text TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Files table (replaces GridFS)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    content_type TEXT,
                    file_path TEXT NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            print("✅ Database tables created successfully")
            
            # Run migrations for existing databases
            self._run_migrations()
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise

    def _run_migrations(self):
        """Run database migrations for schema updates"""
        try:
            cursor = self.conn.cursor()
            
            # Check if rubric columns exist in tests table
            cursor.execute("PRAGMA table_info(tests)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add rubric columns if they don't exist
            if 'rubric_file_id' not in columns:
                cursor.execute("ALTER TABLE tests ADD COLUMN rubric_file_id TEXT")
                print("✅ Added rubric_file_id column to tests table")
            
            if 'rubric_data' not in columns:
                cursor.execute("ALTER TABLE tests ADD COLUMN rubric_data TEXT")
                print("✅ Added rubric_data column to tests table")
                
            if 'rubric_extracted' not in columns:
                cursor.execute("ALTER TABLE tests ADD COLUMN rubric_extracted BOOLEAN DEFAULT 0")
                print("✅ Added rubric_extracted column to tests table")
            
            self.conn.commit()
            
        except Exception as e:
            print(f"❌ Error running migrations: {e}")
            raise
    
    def _setup_default_settings(self):
        """Setup default AI prompts if they don't exist"""
        default_settings = [
            {
                "prompt_type": "ocr",
                "prompt_text": "Extract all text from this image accurately. Preserve formatting and structure."
            },
            {
                "prompt_type": "grading",
                "prompt_text": "Grade this answer accurately. Provide total score, per-question scores, remarks, strengths, and areas for improvement."
            },
            {
                "prompt_type": "rubric_extraction",
                "prompt_text": """Extract the rubric table from this image and return it as a structured JSON format. 
                The rubric typically contains columns like: Concept No., Concept (With Explanation), Example, Status.
                Return the data as: {"rubric": [{"concept_no": "1", "concept": "...", "explanation": "...", "example": "...", "status": "..."}]}
                Preserve all mathematical formulas and formatting in the examples."""
            },
            {
                "prompt_type": "test_extraction",
                "prompt_text": """Extract all questions from this test paper image. 
                Identify and number each question clearly. Preserve mathematical formulas, diagrams descriptions, and formatting.
                Return as JSON: {"questions": [{"question_no": "1", "question_text": "...", "marks": "...", "type": "..."}]}"""
            },
            {
                "prompt_type": "answer_extraction",
                "prompt_text": """Extract the student's answers from this answer sheet image.
                Match answers to question numbers. Preserve mathematical work, diagrams, and step-by-step solutions.
                Return as JSON: {"answers": [{"question_no": "1", "answer_text": "...", "working_shown": "..."}]}"""
            }
        ]
        
        cursor = self.conn.cursor()
        for setting in default_settings:
            cursor.execute(
                "SELECT COUNT(*) FROM settings WHERE prompt_type = ?",
                (setting["prompt_type"],)
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO settings (prompt_type, prompt_text) VALUES (?, ?)",
                    (setting["prompt_type"], setting["prompt_text"])
                )
        self.conn.commit()
    
    def _setup_default_users(self):
        """Setup default users if none exist"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        
        if users_count == 0:
            # Create default users directly to avoid circular import
            import bcrypt
            
            # Create admin user
            admin_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", admin_password, "admin")
            )
            
            # Create student user
            student_password = bcrypt.hashpw("student123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("student", student_password, "student")
            )
            
            self.conn.commit()
            print("Created default users: admin/admin123, student/student123")
    
    def get_cursor(self):
        """Get a database cursor for SQLite operations"""
        return self.conn.cursor()
    
    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False):
        """Execute a SQL query and optionally fetch results"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        if fetch_one:
            result = cursor.fetchone()
            return dict(result) if result else None
        elif fetch_all:
            results = cursor.fetchall()
            return [dict(row) for row in results]
        else:
            self.conn.commit()
            return cursor.lastrowid
    
    def store_file(self, file_data: bytes, filename: str, content_type: str = None) -> str:
        """Store file on disk and return file ID"""
        try:
            file_id = str(uuid.uuid4())
            file_path = self.files_dir / f"{file_id}_{filename}"
            
            # Write file to disk
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Store file metadata in database
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT INTO files (file_id, filename, content_type, file_path, expires_at) 
                   VALUES (?, ?, ?, ?, ?)""",
                (file_id, filename, content_type, str(file_path), 
                 datetime.now() + timedelta(days=7))
            )
            self.conn.commit()
            
            return file_id
        except Exception as e:
            print(f"Error storing file: {e}")
            raise
    
    def get_file(self, file_id: str):
        """Retrieve file from disk"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM files WHERE file_id = ?", (file_id,))
            file_info = cursor.fetchone()
            
            if not file_info:
                raise FileNotFoundError(f"File with ID {file_id} not found")
            
            file_path = Path(file_info['file_path'])
            if not file_path.exists():
                raise FileNotFoundError(f"File {file_path} not found on disk")
            
            with open(file_path, 'rb') as f:
                return {
                    'data': f.read(),
                    'filename': file_info['filename'],
                    'content_type': file_info['content_type']
                }
        except Exception as e:
            print(f"Error retrieving file: {e}")
            raise
    
    def delete_expired_files(self):
        """Delete files older than 7 days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)
            cursor = self.conn.cursor()
            
            # Get expired files
            cursor.execute(
                "SELECT file_path FROM files WHERE expires_at < ?",
                (cutoff_date,)
            )
            expired_files = cursor.fetchall()
            
            # Delete files from disk
            for file_row in expired_files:
                file_path = Path(file_row['file_path'])
                if file_path.exists():
                    file_path.unlink()
            
            # Delete records from database
            cursor.execute("DELETE FROM files WHERE expires_at < ?", (cutoff_date,))
            self.conn.commit()
            
            print(f"Deleted {len(expired_files)} expired files older than {cutoff_date}")
        except Exception as e:
            print(f"Error deleting expired files: {e}")
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            self.connected = False

# Global database manager instance
db_manager = DatabaseManager()
