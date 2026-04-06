# app.py - FastAPI Backend with SQLite Database Integration
import random
import os
import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional, List
from functools import wraps
from fastapi import Request
from fastapi import FastAPI, Depends, HTTPException, status, Query, Body, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import jwt
from jwt.exceptions import PyJWTError
from pydantic import BaseModel
import traceback
from contextlib import asynccontextmanager

from database import (
    get_db_connection,
    hash_password,
    verify_password,
    generate_registration_number,
)
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


SECRET_KEY = "your-very-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic
    try:
        from database import init_database
        if not os.path.exists('library.db'):
            print("🔄 Initializing new database...")
            init_database()
            print("✅ Database created with default admin user")
        else:
            print("✅ Using existing database")
    except Exception:
        print("❌ Database startup error:")
        traceback.print_exc()
        raise

    yield  # application runs after this

    # optional shutdown logic
    try:
        print("🔌 Shutting down application...")
    except Exception:
        print("❌ Error during shutdown:")
        traceback.print_exc()
# ==================== FastAPI Setup ====================
app = FastAPI(
    title="Library Management System",
    description="Backend API for Library Management",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173","https://library-management-system-three-pi.vercel.app/",
                   ],  # add prod origins later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





# JWT Configuration
# class Settings(BaseModel):
#     authjwt_secret_key: str = os.environ.get('JWT_SECRET_KEY', 'library-system-secret-key-2025')
#     authjwt_access_token_expires: int = 60 * 24  # 24 hours in minutes

# @AuthJWT.load_config
# def get_config():
#     return Settings()
def create_access_token(subject: str, user_claims: dict, expires_delta: timedelta = None):
    to_encode = user_claims.copy()
    to_encode.update({
        "sub": subject,
        "exp": datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



# Constants
FINE_PER_DAY = 10
MAX_BOOKS_PER_STUDENT = 3
RETURN_DAYS = 7

# ==================== Pydantic Models ====================
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    email: str
    phone: str

class AddBookRequest(BaseModel):
    title: str
    author: str
    isbn: str
    pages: int
    price: float
    category: str
    quantity: int

class UpdateBookRequest(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    pages: Optional[int] = None
    price: Optional[float] = None
    category: Optional[str] = None
    quantity: Optional[int] = None

class AddStudentRequest(BaseModel):
    username: str
    password: str
    name: str
    email: str
    phone: str

class UpdateStudentRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

class BorrowBookRequest(BaseModel):
    book_id: int

class ReturnBookRequest(BaseModel):
    transaction_id: int

# ==================== Utility Functions ====================
def validate_isbn13(isbn: str) -> bool:
    """Validate ISBN-13 format"""
    isbn = re.sub(r'[-\s]', '', isbn)
    if len(isbn) != 13 or not isbn.isdigit():
        return False
    return True

def row_to_dict(row):
    """Convert sqlite3.Row to dictionary"""
    if row is None:
        return None
    return dict(row)

def rows_to_dict_list(rows):
    """Convert list of sqlite3.Row to list of dictionaries"""
    return [dict(row) for row in rows]

def calculate_fine(due_date_str: str) -> float:
    """Calculate fine for overdue books"""
    if isinstance(due_date_str, str):
        due_date = datetime.fromisoformat(due_date_str)
    else:
        due_date = due_date_str
    today = datetime.now()
    if today > due_date:
        days_overdue = (today - due_date).days
        return days_overdue * FINE_PER_DAY
    return 0

# ==================== Dependency Injection for Roles ====================

async def extract_claims(token: str = Depends(oauth2_scheme)):
    try:
        raw = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # merge claims if you stored some under "claims"/"user_claims"
        user_claims = raw.get("user_claims") or raw.get("claims") or {}
        merged = raw.copy()
        if isinstance(user_claims, dict):
            merged.update(user_claims)
        return merged
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired JWT token")


async def verify_admin(
    claims: dict = Depends(extract_claims),
    request: Request = None
):
    if request is not None and request.method == "OPTIONS":
        return {}
    print("DEBUG verify_admin claims:", claims)
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return claims
async def verify_student(
    claims: dict = Depends(extract_claims),
    request: Request = None
):
    if request is not None and request.method == "OPTIONS":
        return {}
    print("DEBUG verify_student claims:", claims)
    if claims.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    if not claims.get("id"):
        raise HTTPException(status_code=401, detail="Authentication required: missing user id")
    return claims
async def verify_any_user(
    claims: dict = Depends(extract_claims),
    request: Request = None
):
    if request is not None and request.method == "OPTIONS":
        return {}
    print("DEBUG verify_any_user claims:", claims)
    return claims


# ==================== Root & Health Check ====================
@app.get("/")
async def root():
    return {
        "message": "Library Management System API",
        "version": "2.0.0",
        "database": "SQLite",
        "roles": ["admin", "student"]
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ==================== Authentication Routes ====================
@app.post("/api/auth/login")
async def login(data: LoginRequest):
    """Login endpoint for admin or student"""
    try:
        username = data.username.strip()
        password = data.password

        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password are required")

        conn = get_db_connection()

        # Check admin
        admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        if admin and verify_password(password, admin['password']):
            user_claims = {
                'role': admin['role'],
                'name': admin['name'],
                'id': admin['id']
            }
            access_token = create_access_token(username, user_claims)
            conn.close()
            return {
                'success': True,
                'token': access_token,
                'user': {
                    'username': username,
                    'role': admin['role'],
                    'name': admin['name']
                }
            }

        # Check student
        student = conn.execute('SELECT * FROM students WHERE username = ?', (username,)).fetchone()
        if student and verify_password(password, student['password']):
            user_claims = {
                'role': student['role'],
                'id': student['id'],
                'name': student['name'],
                'borrowed_books': student['borrowed_books'],
                'fine_amount': student['fine_amount']
            }
            access_token = create_access_token(username, user_claims)
            conn.close()
            return {
                'success': True,
                'token': access_token,
                'user': {
                    'username': username,
                    'role': student['role'],
                    'id': student['id'],
                    'name': student['name'],
                    'borrowed_books': student['borrowed_books'],
                    'fine_amount': student['fine_amount']
                }
            }

        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/api/auth/register")
async def register(data: RegisterRequest):
    """Register new student"""
    try:
        conn = get_db_connection()
        
        # Check if username exists
        existing = conn.execute('SELECT id FROM students WHERE username = ?', (data.username,)).fetchone()
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Generate registration number
        reg_no = generate_registration_number()
        
        # Hash password
        hashed_pw = hash_password(data.password)
        
        # Insert student
        cursor = conn.execute(
            '''INSERT INTO students (registration_no, username, password, name, email, phone, role)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (reg_no, data.username, hashed_pw, data.name, data.email, data.phone, 'student')
        )
        conn.commit()
        
        new_student = conn.execute('SELECT * FROM students WHERE id = ?', (cursor.lastrowid,)).fetchone()
        conn.close()
        
        student_dict = row_to_dict(new_student)
        student_dict.pop('password', None)
        
        return {
            'success': True,
            'message': 'Student registered successfully',
            'student': student_dict
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/check-username")
async def check_username(username: str = Query(...)):
    """Check if username is available"""
    try:
        conn = get_db_connection()
        
        admin = conn.execute('SELECT id FROM admins WHERE username = ?', (username,)).fetchone()
        student = conn.execute('SELECT id FROM students WHERE username = ?', (username,)).fetchone()
        
        conn.close()
        
        if admin or student:
            return {'available': False}
        return {'available': True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Check failed: {str(e)}")

# ==================== Admin Book Routes ====================
@app.get("/api/admin/books")
async def admin_get_books(claims = Depends(verify_admin)):
    """Get all books (admin only)"""
    try:
        conn = get_db_connection()
        books = conn.execute('SELECT * FROM books ORDER BY created_at DESC').fetchall()
        conn.close()
        return rows_to_dict_list(books)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch books: {str(e)}")


@app.post("/api/admin/books")
async def admin_add_book(data: AddBookRequest, claims = Depends(verify_admin)):
    """Add new book (admin only)"""
    try:
        isbn = data.isbn.strip()
        
        if not validate_isbn13(isbn):
            raise HTTPException(status_code=400, detail="Invalid ISBN-13 format")
        
        conn = get_db_connection()
        
        existing = conn.execute(
            'SELECT id FROM books WHERE isbn = ? OR title = ?',
            (isbn, data.title.strip())
        ).fetchone()
        
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail="Book with this ISBN or title already exists")
        
        quantity = int(data.quantity)
        cursor = conn.execute(
            '''INSERT INTO books (title, author, isbn, pages, price, category, quantity, available)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                data.title.strip(),
                data.author.strip(),
                isbn,
                int(data.pages),
                round(float(data.price), 2),
                data.category.strip(),
                quantity,
                quantity
            )
        )
        conn.commit()
        
        new_book = conn.execute('SELECT * FROM books WHERE id = ?', (cursor.lastrowid,)).fetchone()
        conn.close()
        
        return {'success': True, 'book': row_to_dict(new_book)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add book: {str(e)}")


@app.put("/api/admin/books/{book_id}")
async def admin_update_book(book_id: int = Path(...), data: UpdateBookRequest = Body(...), claims = Depends(verify_admin)):
    """Update book (admin only)"""
    try:
        conn = get_db_connection()
        
        book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
        if not book:
            conn.close()
            raise HTTPException(status_code=404, detail="Book not found")
        
        update_fields, update_values = [], []
        
        if data.title is not None:
            update_fields.append('title = ?')
            update_values.append(data.title.strip())
        if data.author is not None:
            update_fields.append('author = ?')
            update_values.append(data.author.strip())
        if data.pages is not None:
            update_fields.append('pages = ?')
            update_values.append(int(data.pages))
        if data.price is not None:
            update_fields.append('price = ?')
            update_values.append(round(float(data.price), 2))
        if data.category is not None:
            update_fields.append('category = ?')
            update_values.append(data.category.strip())
        if data.quantity is not None:
            new_quantity = int(data.quantity)
            diff = new_quantity - book['quantity']
            update_fields.append('quantity = ?')
            update_values.append(new_quantity)
            update_fields.append('available = ?')
            update_values.append(max(0, book['available'] + diff))
        
        if update_fields:
            update_values.append(book_id)
            query = f"UPDATE books SET {', '.join(update_fields)} WHERE id = ?"
            conn.execute(query, update_values)
            conn.commit()
        
        updated_book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
        conn.close()
        
        return {'success': True, 'book': row_to_dict(updated_book)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update book: {str(e)}")


@app.delete("/api/admin/books/{book_id}")
async def admin_delete_book(book_id: int = Path(...), claims = Depends(verify_admin)):
    """Delete book (admin only)"""
    try:
        conn = get_db_connection()
        
        book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
        if not book:
            conn.close()
            raise HTTPException(status_code=404, detail="Book not found")
        
        borrowed = conn.execute(
            'SELECT id FROM transactions WHERE book_id = ? AND status = ?',
            (book_id, 'borrowed')
        ).fetchone()
        
        if borrowed:
            conn.close()
            raise HTTPException(status_code=400, detail="Cannot delete book that is currently borrowed")
        
        conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Book deleted successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete book: {str(e)}")


@app.get("/api/admin/books/search")
async def admin_search_books(query: str = Query(...), claims = Depends(verify_admin)):
    """Search books by title, author, or ISBN"""
    try:
        conn = get_db_connection()
        search_term = f"%{query}%"
        
        books = conn.execute(
            '''SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?
               ORDER BY created_at DESC''',
            (search_term, search_term, search_term)
        ).fetchall()
        
        conn.close()
        return rows_to_dict_list(books)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ==================== Admin Student Routes ====================
@app.get("/api/admin/students")
async def admin_get_students(claims = Depends(verify_admin)):
    """Get all students (admin only)"""
    try:
        conn = get_db_connection()
        students = conn.execute('SELECT * FROM students ORDER BY created_at DESC').fetchall()
        conn.close()
        
        students_list = rows_to_dict_list(students)
        for student in students_list:
            student.pop('password', None)
        
        return students_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch students: {str(e)}")


@app.post("/api/admin/students")
async def admin_add_student(data: AddStudentRequest, claims = Depends(verify_admin)):
    """Add new student (admin only)"""
    try:
        conn = get_db_connection()
        
        existing = conn.execute('SELECT id FROM students WHERE username = ?', (data.username,)).fetchone()
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail="Username already exists")
        
        reg_no = generate_registration_number()
        hashed_pw = hash_password(data.password)
        
        cursor = conn.execute(
            '''INSERT INTO students (registration_no, username, password, name, email, phone, role)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (reg_no, data.username, hashed_pw, data.name, data.email, data.phone, 'student')
        )
        conn.commit()
        
        new_student = conn.execute('SELECT * FROM students WHERE id = ?', (cursor.lastrowid,)).fetchone()
        conn.close()
        
        student_dict = row_to_dict(new_student)
        student_dict.pop('password', None)
        
        return {'success': True, 'student': student_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add student: {str(e)}")


@app.put("/api/admin/students/{student_id}")
async def admin_update_student(student_id: int = Path(...), data: UpdateStudentRequest = Body(...), claims = Depends(verify_admin)):
    """Update student (admin only)"""
    try:
        conn = get_db_connection()
        
        student = conn.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
        if not student:
            conn.close()
            raise HTTPException(status_code=404, detail="Student not found")
        
        update_fields, update_values = [], []
        
        if data.name is not None:
            update_fields.append('name = ?')
            update_values.append(data.name)
        if data.email is not None:
            update_fields.append('email = ?')
            update_values.append(data.email)
        if data.phone is not None:
            update_fields.append('phone = ?')
            update_values.append(data.phone)
        if data.password is not None and data.password != "":
            update_fields.append('password = ?')
            update_values.append(hash_password(data.password))
        
        if update_fields:
            update_values.append(student_id)
            query = f"UPDATE students SET {', '.join(update_fields)} WHERE id = ?"
            conn.execute(query, update_values)
            conn.commit()
        
        updated_student = conn.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
        conn.close()
        
        student_dict = row_to_dict(updated_student)
        student_dict.pop('password', None)
        
        return {'success': True, 'student': student_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update student: {str(e)}")


@app.delete("/api/admin/students/{student_id}")
async def admin_delete_student(student_id: int = Path(...), claims = Depends(verify_admin)):
    """Delete student (admin only)"""
    try:
        conn = get_db_connection()
        
        student = conn.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
        if not student:
            conn.close()
            raise HTTPException(status_code=404, detail="Student not found")
        
        borrowed = conn.execute(
            'SELECT id FROM transactions WHERE student_id = ? AND status = ?',
            (student_id, 'borrowed')
        ).fetchone()
        
        if borrowed:
            conn.close()
            raise HTTPException(status_code=400, detail="Cannot delete student with borrowed books")
        
        conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Student deleted successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete student: {str(e)}")


@app.get("/api/admin/students/search")
async def admin_search_students(query: str = Query(...), claims = Depends(verify_admin)):
    """Search students by name, email, username, or registration number"""
    try:
        conn = get_db_connection()
        search_term = f"%{query}%"
        
        students = conn.execute(
            '''SELECT * FROM students WHERE name LIKE ? OR email LIKE ? OR username LIKE ? OR registration_no LIKE ?
               ORDER BY created_at DESC''',
            (search_term, search_term, search_term, search_term)
        ).fetchall()
        
        conn.close()
        
        students_list = rows_to_dict_list(students)
        for student in students_list:
            student.pop('password', None)
        
        return students_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ==================== Admin Transaction Routes ====================
@app.get("/api/admin/transactions")
async def admin_get_transactions(claims = Depends(verify_admin)):
    """Get all transactions (admin only)"""
    try:
        conn = get_db_connection()
        transactions = conn.execute(
            '''SELECT t.*, s.name as student_name, s.registration_no, b.title as book_title
               FROM transactions t
               JOIN students s ON t.student_id = s.id
               JOIN books b ON t.book_id = b.id
               ORDER BY t.created_at DESC'''
        ).fetchall()
        conn.close()
        return rows_to_dict_list(transactions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")


@app.get("/api/admin/overdue")
async def admin_get_overdue(claims = Depends(verify_admin)):
    """Get overdue books (admin only)"""
    try:
        conn = get_db_connection()
        overdue = conn.execute(
            '''SELECT t.*, s.name as student_name, s.registration_no, b.title as book_title,
                      strftime('%s', 'now') - strftime('%s', t.due_date) as days_overdue
               FROM transactions t
               JOIN students s ON t.student_id = s.id
               JOIN books b ON t.book_id = b.id
               WHERE t.status = 'borrowed' AND t.due_date < datetime('now')
               ORDER BY t.due_date ASC'''
        ).fetchall()
        conn.close()
        return rows_to_dict_list(overdue)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch overdue books: {str(e)}")


@app.post("/api/admin/return/{transaction_id}")
async def admin_return_book(transaction_id: int = Path(...), claims = Depends(verify_admin)):
    """Process book return (admin only)"""
    try:
        conn = get_db_connection()
        
        transaction = conn.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,)).fetchone()
        if not transaction:
            conn.close()
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction['status'] != 'borrowed':
            conn.close()
            raise HTTPException(status_code=400, detail="Book not currently borrowed")
        
        fine_amount = calculate_fine(transaction['due_date'])
        
        conn.execute(
            '''UPDATE transactions SET status = ?, return_date = ?, fine_amount = ?
               WHERE id = ?''',
            ('returned', datetime.now().isoformat(), fine_amount, transaction_id)
        )
        
        conn.execute(
            'UPDATE books SET available = available + 1 WHERE id = ?',
            (transaction['book_id'],)
        )
        
        conn.execute(
            'UPDATE students SET borrowed_books = borrowed_books - 1, fine_amount = fine_amount + ? WHERE id = ?',
            (fine_amount, transaction['student_id'])
        )
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': 'Book returned successfully',
            'fine_amount': fine_amount
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to return book: {str(e)}")


@app.get("/api/admin/stats")
async def admin_get_stats(claims = Depends(verify_admin)):
    """Get admin dashboard statistics"""
    try:
        conn = get_db_connection()
        
        total_books = conn.execute('SELECT COUNT(*) as count FROM books').fetchone()['count']
        total_students = conn.execute('SELECT COUNT(*) as count FROM students').fetchone()['count']
        active_borrows = conn.execute(
            'SELECT COUNT(*) as count FROM transactions WHERE status = ?', ('borrowed',)
        ).fetchone()['count']
        overdue_books = conn.execute(
            '''SELECT COUNT(*) as count FROM transactions
               WHERE status = ? AND due_date < datetime('now')''', ('borrowed',)
        ).fetchone()['count']
        total_transactions = conn.execute(
            'SELECT COUNT(*) as count FROM transactions'
        ).fetchone()['count']
        total_fines = conn.execute(
            'SELECT SUM(fine_amount) as total FROM transactions WHERE fine_amount > 0'
        ).fetchone()['total']
        conn.close()
        
        return {
            'total_books': total_books,
            'total_students': total_students,
            'active_borrows': active_borrows,
            'overdue_books': overdue_books,
            'total_transactions': total_transactions,
            'total_fines': total_fines if total_fines is not None else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")

# ==================== Student Routes ====================
@app.get("/api/student/books")
async def student_get_available_books(claims = Depends(verify_student)):
    """Get available books for borrowing"""
    try:
        conn = get_db_connection()
        books = conn.execute('SELECT * FROM books ORDER BY title ASC').fetchall()
        conn.close()
        return rows_to_dict_list(books)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch books: {str(e)}")

def get_next_transaction_id():
    """Generate next transaction ID in form TXN0001 based on highest id."""
    conn = get_db_connection()
    try:
        last_id_row = conn.execute('SELECT MAX(id) as max_id FROM transactions').fetchone()
        max_id = last_id_row['max_id'] if last_id_row else None
        if not max_id:
            next_num = 1
        else:
            next_num = int(max_id) + 1
        return f'TXN{str(next_num).zfill(4)}'
    finally:
        conn.close()


@app.get("/api/student/my-books")
async def student_get_my_books(claims = Depends(verify_student)):
    """Get student's borrowed books"""
    try:
        student_id = claims.get('id')
        conn = get_db_connection()
        transactions = conn.execute(
            '''SELECT t.*, b.title as book_title, b.author as book_author, b.isbn
               FROM transactions t
               JOIN books b ON t.book_id = b.id
               WHERE t.student_id = ? AND t.status = 'borrowed'
               ORDER BY t.borrow_date DESC''',
            (student_id,)
        ).fetchall()
        conn.close()
        return [
            {
                "id": row["id"],
                "transaction_id": row["transaction_id"],
                "borrow_date": row["borrow_date"],
                "due_date": row["due_date"],
                "fine": row["fine_amount"],
                "book": {
                    "title": row["book_title"],
                    "author": row["book_author"]
                }
                # add other fields as needed
            }
            for row in transactions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch borrowed books: {str(e)}")

@app.post("/api/student/borrow")
async def student_borrow_book(data: BorrowBookRequest = Body(...), claims = Depends(verify_student)):
    """
    Borrow a book with improved error handling, validation, and concurrency control.
    
    Changes:
    - Validates all inputs before DB operations
    - Retries on transient database locks
    - Checks for duplicate borrow attempts
    - Logs detailed error messages
    - Better transaction rollback handling
    """
    conn = None
    try:
        # === STEP 1: Validate student identity ===
        student_id = claims.get('id')
        if not student_id or not isinstance(student_id, int):
            raise HTTPException(
                status_code=401, 
                detail="Invalid student credentials: missing or malformed id in token"
            )
        
        # === STEP 2: Validate book_id ===
        if not isinstance(data.book_id, int) or data.book_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid book ID: must be a positive integer"
            )
        
        # === STEP 3: Get database connection with retry logic ===
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                conn = get_db_connection()
                break
            except Exception as db_error:
                last_error = db_error
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(0.1)  # Small backoff
        
        if not conn:
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable. Please try again in a moment."
            )
        
        # === STEP 4: Start transaction with immediate write lock ===
        try:
            conn.execute("BEGIN IMMEDIATE;")
        except Exception as lock_error:
            raise HTTPException(
                status_code=503,
                detail=f"Database is busy. Please try again. Error: {str(lock_error)}"
            )
        
        try:
            # === STEP 5: Fetch and validate student ===
            student_row = conn.execute(
                'SELECT * FROM students WHERE id = ?', 
                (student_id,)
            ).fetchone()
            
            if not student_row:
                conn.rollback()
                raise HTTPException(status_code=404, detail="Student not found in database")
            
            student = dict(student_row)
            borrowed_count = int(student.get('borrowed_books', 0))
            student_name = student.get('name', 'Unknown')
            
            # === STEP 6: Check borrow limit ===
            if borrowed_count >= MAX_BOOKS_PER_STUDENT:
                conn.rollback()
                raise HTTPException(
                    status_code=400, 
                    detail=f"Borrow limit reached. You have {borrowed_count}/{MAX_BOOKS_PER_STUDENT} books. Please return a book first."
                )
            
            # === STEP 7: Fetch and validate book ===
            book_row = conn.execute(
                'SELECT * FROM books WHERE id = ?', 
                (data.book_id,)
            ).fetchone()
            
            if not book_row:
                conn.rollback()
                raise HTTPException(status_code=404, detail=f"Book with ID {data.book_id} not found")
            
            book = dict(book_row)
            available = int(book.get('available', 0))
            book_title = book.get('title', 'Unknown')
            
            if available <= 0:
                conn.rollback()
                raise HTTPException(
                    status_code=400, 
                    detail=f"'{book_title}' is not available. Total copies: {book.get('quantity', 0)}, Available: {available}"
                )
            
            # === STEP 8: Check for duplicate borrow (prevent same book twice) ===
            existing_borrow = conn.execute(
                'SELECT id FROM transactions WHERE student_id = ? AND book_id = ? AND status = ?',
                (student_id, data.book_id, 'borrowed')
            ).fetchone()
            
            if existing_borrow:
                conn.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"You have already borrowed '{book_title}'. Please return it before borrowing another copy."
                )
            
            # === STEP 9: Create borrow transaction ===
            borrow_date = datetime.now()
            due_date = borrow_date + timedelta(days=RETURN_DAYS)
            
            cur = conn.cursor()
            next_txn_id = get_next_transaction_id()
            # Now include next_txn_id in the insert:
            cur.execute('''
                INSERT INTO transactions
                (transaction_id, student_id, student_registration_no, book_id, borrow_date, due_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                next_txn_id, student_id, student.get('registration_no', ''), data.book_id, borrow_date.isoformat(), due_date.isoformat(), 'borrowed'
            ))

            
            trans_id = cur.lastrowid
            
            # === STEP 10: Retrieve trigger-generated transaction_id ===
            txn_row = conn.execute(
                'SELECT transaction_id FROM transactions WHERE id = ?', 
                (trans_id,)
            ).fetchone()
            
            transaction_code = (
                txn_row['transaction_id'] 
                if txn_row and txn_row['transaction_id'] 
                else f"TXN{str(trans_id).zfill(4)}"
            )
            
            # === STEP 11: Update book availability ===
            conn.execute(
                'UPDATE books SET available = available - 1 WHERE id = ?', 
                (data.book_id,)
            )
            
            # === STEP 12: Update student borrowed count ===
            conn.execute(
                'UPDATE students SET borrowed_books = borrowed_books + 1 WHERE id = ?', 
                (student_id,)
            )
            
            # === STEP 13: Commit all changes ===
            conn.commit()
            
            # === STEP 14: Return success response ===
            return {
                'success': True,
                'message': f'Book "{book_title}" borrowed successfully',
                'transaction_id': transaction_code,
                'due_date': due_date.isoformat(),
                'days_to_return': RETURN_DAYS,
                'book': {
                    'id': book.get('id'),
                    'title': book_title,
                    'author': book.get('author')
                },
                'student': {
                    'id': student_id,
                    'name': student_name,
                    'borrowed_count': borrowed_count + 1,
                    'max_borrow': MAX_BOOKS_PER_STUDENT
                }
            }
        
        except HTTPException:
            # Re-raise HTTP exceptions after rollback
            if conn:
                try:
                    conn.rollback()
                except Exception as rb_error:
                    print(f"WARNING: Rollback failed: {rb_error}", flush=True)
            raise
        
        except Exception as inner_error:
            # Catch unexpected errors during transaction
            if conn:
                try:
                    conn.rollback()
                except Exception as rb_error:
                    print(f"WARNING: Rollback failed after inner error: {rb_error}", flush=True)
            
            error_msg = f"Transaction processing failed: {str(inner_error)}"
            print(f"ERROR in student_borrow_book (inner): {error_msg}", flush=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    except HTTPException:
        raise
    
    except Exception as error:
        # Catch unexpected errors (e.g., connection issues)
        error_msg = f"Borrow operation failed: {str(error)}"
        print(f"ERROR in student_borrow_book (outer): {error_msg}", flush=True)
        raise HTTPException(status_code=500, detail=error_msg)
    
    finally:
        # Always close connection
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                print(f"WARNING: Error closing database connection: {close_error}", flush=True)


@app.post("/api/student/return")
async def student_return_book(data: ReturnBookRequest, claims = Depends(verify_student)):
    """Return a borrowed book"""
    try:
        student_id = claims.get('id')
        conn = get_db_connection()
        
        transaction = conn.execute('SELECT * FROM transactions WHERE id = ?', (data.transaction_id,)).fetchone()
        if not transaction or transaction['student_id'] != student_id:
            conn.close()
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction['status'] != 'borrowed':
            conn.close()
            raise HTTPException(status_code=400, detail="Book not currently borrowed")
        
        fine_amount = calculate_fine(transaction['due_date'])
        
        conn.execute(
            '''UPDATE transactions SET status = ?, return_date = ?, fine_amount = ?
               WHERE id = ?''',
            ('returned', datetime.now().isoformat(), fine_amount, data.transaction_id)
        )
        
        conn.execute('UPDATE books SET available = available + 1 WHERE id = ?', (transaction['book_id'],))
        conn.execute('UPDATE students SET borrowed_books = borrowed_books - 1, fine_amount = fine_amount + ? WHERE id = ?',
                     (fine_amount, student_id))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': 'Book returned successfully',
            'fine_amount': fine_amount
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to return book: {str(e)}")


@app.get("/api/student/fines")
async def student_get_fines(claims = Depends(verify_student)):
    """Get student's fine information"""
    try:
        student_id = claims.get('id')
        conn = get_db_connection()
        
        student = conn.execute('SELECT fine_amount, borrowed_books FROM students WHERE id = ?', (student_id,)).fetchone()
        conn.close()
        
        return {
            'fine_amount': student['fine_amount'],
            'borrowed_books': student['borrowed_books']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch fines: {str(e)}")


@app.get("/api/student/history")
async def student_get_transaction_history(claims = Depends(verify_student)):
    """Get student's complete transaction history"""
    try:
        student_id = claims.get('id')
        conn = get_db_connection()
        
        transactions = conn.execute(
            '''SELECT t.*, b.title, b.author
               FROM transactions t
               JOIN books b ON t.book_id = b.id
               WHERE t.student_id = ?
               ORDER BY t.created_at DESC''',
            (student_id,)
        ).fetchall()
        
        conn.close()
        return rows_to_dict_list(transactions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


# ==================== Error Handlers ====================
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)