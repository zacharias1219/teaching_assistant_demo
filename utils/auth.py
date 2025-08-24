import bcrypt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict
from utils.database import db_manager

class AuthManager:
    def __init__(self):
        self.failed_attempts = {}  # In-memory tracking for demo
        self.lockout_duration = timedelta(minutes=5)
        self.max_attempts = 5
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, username: str, password: str, role: str) -> bool:
        """Create new user in database"""
        try:
            # Check if user already exists
            existing = db_manager.execute_query(
                "SELECT COUNT(*) as count FROM users WHERE username = ?",
                (username,),
                fetch_one=True
            )
            
            if existing and existing['count'] > 0:
                return False
            
            password_hash = self.hash_password(password)
            
            db_manager.execute_query(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            
            return True
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data if successful"""
        # Check if user is locked out
        if self.is_locked_out(username):
            return None
        
        try:
            user = db_manager.execute_query(
                "SELECT * FROM users WHERE username = ?",
                (username,),
                fetch_one=True
            )
            
            if not user:
                self.record_failed_attempt(username)
                return None
            
            if self.verify_password(password, user['password_hash']):
                # Clear failed attempts on successful login
                if username in self.failed_attempts:
                    del self.failed_attempts[username]
                
                return {
                    "user_id": str(user['id']),
                    "username": user['username'],
                    "role": user['role']
                }
            else:
                self.record_failed_attempt(username)
                return None
                
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        now = datetime.utcnow()
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        
        self.failed_attempts[username].append(now)
        
        # Clean old attempts (older than lockout duration)
        cutoff = now - self.lockout_duration
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username] 
            if attempt > cutoff
        ]
    
    def is_locked_out(self, username: str) -> bool:
        """Check if user is locked out due to failed attempts"""
        if username not in self.failed_attempts:
            return False
        
        # Clean old attempts first
        now = datetime.utcnow()
        cutoff = now - self.lockout_duration
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username] 
            if attempt > cutoff
        ]
        
        return len(self.failed_attempts[username]) >= self.max_attempts
    
    def get_lockout_time_remaining(self, username: str) -> Optional[timedelta]:
        """Get remaining lockout time for user"""
        if not self.is_locked_out(username):
            return None
        
        if username not in self.failed_attempts:
            return None
        
        # Find the oldest attempt in the current window
        oldest_attempt = min(self.failed_attempts[username])
        unlock_time = oldest_attempt + self.lockout_duration
        remaining = unlock_time - datetime.utcnow()
        
        return remaining if remaining.total_seconds() > 0 else None

# Global auth manager instance
auth_manager = AuthManager()