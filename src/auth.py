
import sqlite3
import os
import datetime
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import BaseModel

# ==============================================================================
# 1. ⚙️ KONFIGURASI AUTH
# ==============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "chem_portal_secret_key_change_me_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Database SQLite untuk User
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "users.db")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class UserRegister(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# ==============================================================================
# 2. 🗄️ DATABASE HELPER
# ==============================================================================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_user_by_username(username: str):
    print(f"DEBUG: Fetching user {username}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username, hashed_password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user:
             print(f"DEBUG: User {username} found")
        else:
             print(f"DEBUG: User {username} NOT found")
        return user
    except Exception as e:
        print(f"DEBUG: Error fetching user {username}: {e}")
        return None

def create_user(username: str, hashed_password: str):
    print(f"DEBUG: Attempting to create user {username}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        print(f"DEBUG: User {username} created successfully")
        return True
    except sqlite3.IntegrityError as e:
        print(f"DEBUG: Integrity error for {username}: {e}")
        return False
    except Exception as e:
        print(f"DEBUG: Unexpected error creating user {username}: {e}")
        return False

# Jalankan init saat module di-load
init_db()

# ==============================================================================
# 3. 🔐 AUTH LOGIC
# ==============================================================================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None
