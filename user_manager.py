"""
User Management Module
Handles user registration, login, roles, sessions, and project workspaces
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserManager:
    """Manages user accounts, authentication, roles, and project workspaces."""
    
    USER_ROLES = {
        'public': 'Public User',
        'student': 'Student',
        'professional': 'Professional',
        'admin': 'Admin'
    }
    
    def __init__(self, data_directory: str = "./user_data"):
        self.data_directory = Path(data_directory)
        self.users_file = self.data_directory / "users.json"
        self.sessions_file = self.data_directory / "sessions.json"
        self.data_directory.mkdir(exist_ok=True)
        self._load_users()
        self._load_sessions()
    
    def _load_users(self):
        """Load user data from file."""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except Exception as e:
                logger.error(f"Error loading users: {e}")
                self.users = {}
        else:
            self.users = {}
            self._save_users()
    
    def _save_users(self):
        """Save user data to file."""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def _load_sessions(self):
        """Load session data from file."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
            except Exception as e:
                logger.error(f"Error loading sessions: {e}")
                self.sessions = {}
        else:
            self.sessions = {}
            self._save_sessions()
    
    def _save_sessions(self):
        """Save session data to file."""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, email: str, password: str, role: str = 'public', 
                     name: Optional[str] = None) -> Dict:
        """Register a new user."""
        if email in self.users:
            return {'success': False, 'message': 'Email already registered'}
        
        if role not in self.USER_ROLES:
            role = 'public'
        
        user_id = f"user_{len(self.users) + 1}"
        self.users[email] = {
            'user_id': user_id,
            'email': email,
            'password_hash': self._hash_password(password),
            'role': role,
            'name': name or email.split('@')[0],
            'created_at': datetime.now().isoformat(),
            'projects': [],
            'settings': {}
        }
        self._save_users()
        
        logger.info(f"User registered: {email} ({role})")
        return {'success': True, 'message': 'User registered successfully', 'user_id': user_id}
    
    def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data."""
        if email not in self.users:
            return None
        
        user = self.users[email]
        password_hash = self._hash_password(password)
        
        if user['password_hash'] == password_hash:
            return {
                'user_id': user['user_id'],
                'email': user['email'],
                'role': user['role'],
                'name': user['name'],
                'projects': user.get('projects', [])
            }
        
        return None
    
    def create_session(self, user_id: str, email: str) -> str:
        """Create a new session and return session ID."""
        import secrets
        session_id = secrets.token_urlsafe(32)
        
        self.sessions[session_id] = {
            'user_id': user_id,
            'email': email,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        self._save_sessions()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data by session ID."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session['last_activity'] = datetime.now().isoformat()
            self._save_sessions()
            return session
        return None
    
    def get_user(self, email: str) -> Optional[Dict]:
        """Get user data by email."""
        return self.users.get(email)
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user data by user ID."""
        for email, user in self.users.items():
            if user['user_id'] == user_id:
                return user
        return None
    
    def create_project(self, user_id: str, project_name: str, 
                      description: Optional[str] = None) -> Dict:
        """Create a new project workspace for a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        project_id = f"project_{len(user.get('projects', [])) + 1}_{user_id}"
        project = {
            'project_id': project_id,
            'name': project_name,
            'description': description or '',
            'created_at': datetime.now().isoformat(),
            'modified_at': datetime.now().isoformat(),
            'team_members': [user_id],
            'documents': [],
            'sites': [],
            'artifacts': [],
            'maps': [],
            'chat_history': []
        }
        
        if 'projects' not in user:
            user['projects'] = []
        user['projects'].append(project)
        
        # Create project directory
        project_dir = self.data_directory / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        self._save_users()
        
        logger.info(f"Project created: {project_name} for user {user_id}")
        return {'success': True, 'project': project, 'project_id': project_id}
    
    def get_user_projects(self, user_id: str) -> List[Dict]:
        """Get all projects for a user."""
        user = self.get_user_by_id(user_id)
        if user:
            return user.get('projects', [])
        return []
    
    def add_team_member(self, project_id: str, user_id: str, member_email: str) -> Dict:
        """Add a team member to a project."""
        member_user = self.get_user(member_email)
        if not member_user:
            return {'success': False, 'message': 'User not found'}
        
        # Find project in all users
        for email, user in self.users.items():
            for project in user.get('projects', []):
                if project['project_id'] == project_id:
                    if user_id not in project.get('team_members', []):
                        return {'success': False, 'message': 'You do not have permission to add members'}
                    
                    if member_user['user_id'] not in project['team_members']:
                        project['team_members'].append(member_user['user_id'])
                        project['modified_at'] = datetime.now().isoformat()
                        self._save_users()
                        return {'success': True, 'message': 'Team member added'}
                    return {'success': False, 'message': 'User already in project'}
        
        return {'success': False, 'message': 'Project not found'}
    
    def update_user_settings(self, user_id: str, settings: Dict) -> bool:
        """Update user settings."""
        user = self.get_user_by_id(user_id)
        if user:
            if 'settings' not in user:
                user['settings'] = {}
            user['settings'].update(settings)
            self._save_users()
            return True
        return False
    
    def get_user_settings(self, user_id: str) -> Dict:
        """Get user settings."""
        user = self.get_user_by_id(user_id)
        if user:
            return user.get('settings', {})
        return {}
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission based on role."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        role = user.get('role', 'public')
        
        # Permission matrix
        permissions = {
            'public': ['view', 'upload_documents'],
            'student': ['view', 'upload_documents', 'create_projects', 'export_data'],
            'professional': ['view', 'upload_documents', 'create_projects', 'export_data', 
                           'advanced_analysis', 'team_collaboration', 'compliance_tools'],
            'admin': ['all']
        }
        
        if role == 'admin':
            return True
        
        role_perms = permissions.get(role, [])
        return permission in role_perms


# Simple session storage for Streamlit
class StreamlitSessionManager:
    """Manages user sessions in Streamlit."""
    
    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager
    
    def get_current_user(self, session_state) -> Optional[Dict]:
        """Get current logged-in user from session state."""
        if 'user_session_id' in session_state:
            session = self.user_manager.get_session(session_state.user_session_id)
            if session:
                user = self.user_manager.get_user_by_id(session['user_id'])
                if user:
                    return {
                        'user_id': user['user_id'],
                        'email': user['email'],
                        'role': user['role'],
                        'name': user['name']
                    }
        return None
    
    def login(self, session_state, email: str, password: str) -> Dict:
        """Login user and create session."""
        user_data = self.user_manager.authenticate(email, password)
        if user_data:
            session_id = self.user_manager.create_session(user_data['user_id'], email)
            session_state.user_session_id = session_id
            session_state.user_data = user_data
            return {'success': True, 'message': 'Login successful'}
        return {'success': False, 'message': 'Invalid email or password'}
    
    def logout(self, session_state):
        """Logout user and clear session."""
        if 'user_session_id' in session_state:
            # Optionally remove session from storage
            del session_state.user_session_id
        if 'user_data' in session_state:
            del session_state.user_data
        session_state.messages = []  # Clear chat history
    
    def is_logged_in(self, session_state) -> bool:
        """Check if user is logged in."""
        return 'user_session_id' in session_state and self.get_current_user(session_state) is not None

