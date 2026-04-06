# Library Management System — Design Patterns, Architecture & Tech Stack

> **Purpose**: Interview-ready reference document explaining every architectural and design decision made in this project.

---

## Table of Contents

1. [Tech Stack & Justification](#1-tech-stack--justification)
2. [High-Level Design (HLD)](#2-high-level-design-hld)
3. [Low-Level Design (LLD) — Design Patterns](#3-low-level-design-lld--design-patterns)
   - [3.1 Layered / N-Tier Architecture](#31-layered--n-tier-architecture)
   - [3.2 Repository Pattern](#32-repository-pattern)
   - [3.3 Service Layer / Façade Pattern](#33-service-layer--façade-pattern)
   - [3.4 Factory Pattern](#34-factory-pattern)
   - [3.5 Dependency Injection (DI)](#35-dependency-injection-di)
   - [3.6 Singleton Pattern](#36-singleton-pattern)
   - [3.7 Template Method Pattern](#37-template-method-pattern)
   - [3.8 DTO / Data Transfer Object Pattern](#38-dto--data-transfer-object-pattern)
   - [3.9 Middleware / Chain of Responsibility Pattern](#39-middleware--chain-of-responsibility-pattern)
   - [3.10 Custom Exception Hierarchy](#310-custom-exception-hierarchy)
4. [Database Design](#4-database-design)
5. [Interview Q&A Cheat Sheet](#5-interview-qa-cheat-sheet)

---

## 1. Tech Stack & Justification

| Layer                 | Technology                               | Why This Choice?                                                                                                                                                                                                              |
| --------------------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Backend Framework** | **FastAPI** (Python)                     | Async-first, auto-generated OpenAPI/Swagger docs, built-in request validation via Pydantic, dependency injection system, high performance (Starlette + Uvicorn). Preferred over Flask/Django for modern REST API development. |
| **ORM**               | **SQLAlchemy**                           | The most mature Python ORM. Supports both Core (raw SQL) and ORM (object mapping) paradigms. Database-agnostic — can switch from SQLite to PostgreSQL without changing model code.                                            |
| **Database**          | **SQLite** (dev) / **PostgreSQL** (prod) | SQLite for zero-config development; PostgreSQL for production scalability, ACID compliance, and concurrent write support. The `DATABASE_URL` config makes switching seamless.                                                 |
| **Authentication**    | **JWT (JSON Web Tokens)** via `PyJWT`    | Stateless authentication — no server-side session storage needed. Scalable across multiple server instances. Token contains role (`admin`/`student`) for authorization without extra DB queries.                              |
| **Password Hashing**  | **bcrypt**                               | Industry-standard adaptive hashing algorithm. Resistant to brute-force attacks due to configurable work factor (`gensalt()`). Preferred over MD5/SHA256 which are too fast for password storage.                              |
| **Validation**        | **Pydantic v2**                          | Automatic request body validation, type coercion, and serialization. `pydantic-settings` for environment variable loading. Deeply integrated with FastAPI.                                                                    |
| **Server**            | **Uvicorn**                              | ASGI server, lightweight, supports hot-reload in development. Built on `uvloop` for high throughput.                                                                                                                          |
| **Containerization**  | **Docker + Docker Compose**              | Consistent deployment across environments. Compose orchestrates backend + database services.                                                                                                                                  |
| **Frontend**          | **Vanilla HTML/CSS/JS**                  | Lightweight, no build step required. Communicates with backend via REST API (fetch). Suitable for this scale of application.                                                                                                  |

### Why FastAPI over Django/Flask?

| Criteria             | Django        | Flask    | FastAPI ✅          |
| -------------------- | ------------- | -------- | ------------------- |
| Auto API docs        | ✗ (needs DRF) | ✗        | ✅ Built-in Swagger |
| Async support        | Partial       | ✗        | ✅ Native           |
| Type safety          | ✗             | ✗        | ✅ Pydantic         |
| Dependency injection | ✗             | ✗        | ✅ Built-in         |
| Performance          | Moderate      | Moderate | ✅ High             |
| Learning curve       | Steep         | Low      | Low-Medium          |

---

## 2. High-Level Design (HLD)

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Admin Panel  │  │ Student Portal│  │ API Consumer (curl)│ │
│  │  (HTML/JS)   │  │  (HTML/JS)    │  │                   │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘  │
└─────────┼─────────────────┼───────────────────┼─────────────┘
          │ HTTP/REST       │ HTTP/REST         │
          ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              FastAPI Application                       │  │
│  │  ┌──────────┐ ┌──────────────┐ ┌───────────────────┐  │  │
│  │  │   CORS   │ │  Logging     │ │ Exception Handlers │  │  │
│  │  │Middleware │ │ Middleware   │ │  (Global)          │  │  │
│  │  └──────────┘ └──────────────┘ └───────────────────┘  │  │
│  └───────────────────────┬───────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Auth Routes │ │ Admin Routes │ │Student Routes│
│ /api/auth/*  │ │ /api/admin/* │ │/api/student/*│
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ AuthService   │ │ BookService  │ │ TransactionService   │ │
│  │              │ │              │ │                      │ │
│  │ - authenticate│ │ - add_book   │ │ - borrow_book        │ │
│  │ - register    │ │ - update_book│ │ - return_book        │ │
│  │ - JWT mgmt    │ │ - search     │ │ - calculate_fines    │ │
│  └──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘ │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   REPOSITORY LAYER                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              BaseRepository<T>  (Generic CRUD)         │  │
│  └────────┬──────────┬──────────────┬────────────────────┘  │
│           │          │              │                        │
│  ┌────────▼───┐ ┌────▼───────┐ ┌───▼──────────────┐        │
│  │ AdminRepo  │ │ BookRepo   │ │ TransactionRepo  │        │
│  │ StudentRepo│ │            │ │                  │        │
│  └────────────┘ └────────────┘ └──────────────────┘        │
└─────────────────────────┬───────────────────────────────────┘
                          │ SQLAlchemy ORM
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                             │
│            SQLite (Dev) / PostgreSQL (Prod)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  admins  │ │ students │ │  books   │ │ transactions │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Key HLD Decisions

| Decision                           | Rationale                                                                                                                                              |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Monolithic architecture**        | Appropriate for the scale. Microservices would add unnecessary complexity (service discovery, inter-service communication) for a single-domain system. |
| **REST API**                       | Standard, well-understood, cacheable. CRUD operations on resources (books, students, transactions) map naturally to HTTP verbs.                        |
| **Stateless authentication (JWT)** | No server-side session store → horizontally scalable. Token contains user role for zero-DB-query authorization.                                        |
| **SQLite → PostgreSQL via config** | `DATABASE_URL` abstraction allows environment-specific DBs without code changes. SQLite for dev speed, PostgreSQL for production reliability.          |
| **CORS middleware**                | Frontend served separately from backend → cross-origin requests must be explicitly allowed.                                                            |

---

## 3. Low-Level Design (LLD) — Design Patterns

### 3.1 Layered / N-Tier Architecture

**Pattern**: Separation of concerns into distinct layers with uni-directional dependencies.

```
Routes (Controllers)  →  Services (Business Logic)  →  Repositories (Data Access)  →  Models (ORM)
        ↑                                                                                  ↓
   Schemas (DTOs)                                                                      Database
```

**Where applied**: Entire project structure.

```
app/
├── routes/          # Layer 1: HTTP request handling (Controller)
├── services/        # Layer 2: Business logic
├── repositories/    # Layer 3: Data access
├── models/          # Layer 4: ORM entities
├── schemas/         # DTOs for request/response validation
├── middleware/       # Cross-cutting concerns
├── dependencies.py  # DI providers
├── exceptions.py    # Error hierarchy
└── config.py        # Configuration
```

**Why this pattern?**

- **Single Responsibility**: Each layer has exactly one job. Routes don't know SQL. Services don't know HTTP status codes. Repositories don't know business rules.
- **Testability**: You can unit-test services by mocking repositories. You can test repositories against an in-memory DB without FastAPI.
- **Maintainability**: Changing the database (e.g., SQLite → PostgreSQL) only affects the repository and config layers.
- **Team scalability**: Different developers can work on different layers simultaneously.

---

### 3.2 Repository Pattern

**Pattern**: Abstract the data access layer behind a clean interface, hiding database query details from business logic.

**Where applied**: `app/repositories/`

```python
# base.py — Generic base with common CRUD
class BaseRepository(Generic[ModelType]):
    def get_by_id(self, id: int) -> Optional[ModelType]: ...
    def get_all(self, skip, limit) -> List[ModelType]: ...
    def create(self, obj) -> ModelType: ...
    def update(self, obj) -> ModelType: ...
    def delete(self, obj) -> None: ...

# book_repo.py — Domain-specific queries
class BookRepository(BaseRepository[Book]):
    def get_by_isbn(self, isbn: str): ...
    def search(self, query: str): ...
```

**Why this pattern?**

- **Decouples business logic from ORM**: If we switch from SQLAlchemy to SQLModel or raw SQL, only repositories change.
- **Prevents query duplication**: Common filters (e.g., "find overdue transactions") are defined once in the repository and reused across multiple services.
- **Encourages DRY**: `BaseRepository` provides 5 generic methods that all 4 entity repositories inherit automatically.
- **Testable**: Services can be tested with mock repositories — no real database needed.

**Interview tip**: _"I chose the Repository Pattern to create a clear boundary between business logic and data access. This means if I switch from SQLite to PostgreSQL, or even to a NoSQL database, I only modify repository classes — zero changes in the service layer."_

---

### 3.3 Service Layer / Façade Pattern

**Pattern**: Encapsulate complex business logic behind simple function interfaces. Services orchestrate multiple repositories and enforce domain rules.

**Where applied**: `app/services/`

```python
# transaction_service.py — Orchestrates 3 repositories
def borrow_book(db, student_id, book_id):
    book_repo = BookRepository(db)       # Data access
    student_repo = StudentRepository(db)  # Data access
    txn_repo = TransactionRepository(db)  # Data access

    # Business Rules (not in route, not in repo):
    # 1. Book must exist and be available
    # 2. Student must not exceed MAX_BOOKS_PER_STUDENT
    # 3. No duplicate active borrows
    # 4. Create transaction + update book availability + update student count
```

**Why this pattern?**

- **Keeps routes thin**: Route handlers are 1-3 lines — they just validate input (via schemas) and delegate to services.
- **Centralizes business rules**: The "borrow limit" rule lives in `transaction_service`, not scattered across routes.
- **Transaction integrity**: A single service method can coordinate multiple repository operations within one database transaction.
- **Reusability**: `admin_return_book()` reuses `return_book()` — different entry points, same core logic.

**Interview tip**: _"The Service Layer acts as a Façade — routes don't need to know which repositories are involved or what validation rules exist. They just call `borrow_book()` and get a result or an exception."_

---

### 3.4 Factory Pattern

**Pattern**: Use a factory function to create and configure complex objects.

**Where applied**: `app/__init__.py` → `create_app()`

```python
def create_app() -> FastAPI:
    app = FastAPI(title="Library Management System", ...)

    # Configure in sequence:
    app.add_middleware(CORSMiddleware, ...)     # Step 1: CORS
    app.add_middleware(RequestLoggingMiddleware) # Step 2: Logging
    register_exception_handlers(app)            # Step 3: Error handlers
    app.include_router(auth.router, ...)        # Step 4: Routes
    app.include_router(admin.router, ...)
    app.include_router(student.router, ...)

    return app
```

**Why this pattern?**

- **Encapsulates creation complexity**: 6+ configuration steps are hidden behind a single `create_app()` call.
- **Testability**: You can call `create_app()` with different settings for testing (e.g., test database, disabled CORS).
- **Avoids circular imports**: Routes are imported inside the factory, not at module level.
- **Industry standard**: Flask, Django, and FastAPI all recommend the factory pattern for production applications.

**Interview tip**: _"The Factory Pattern lets me create differently-configured app instances for different environments — production uses PostgreSQL + strict CORS, testing uses SQLite + relaxed CORS — without duplicating setup code."_

---

### 3.5 Dependency Injection (DI)

**Pattern**: Provide dependencies (DB sessions, auth context) to functions from the outside, rather than having them create their own.

**Where applied**: `app/dependencies.py` + FastAPI's `Depends()` system

```python
# Dependency providers
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db       # Injected into route handler
    finally:
        db.close()     # Auto-cleanup after request

def require_admin(claims: dict = Depends(get_current_user)) -> dict:
    if claims.get("role") != "admin":
        raise ForbiddenError("Admin access required")
    return claims

# Usage in route — dependencies are injected automatically
@router.get("/books")
def get_books(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    return book_service.get_books(db)
```

**Why this pattern?**

- **Automatic lifecycle management**: Database sessions are created before and closed after each request — no manual cleanup needed.
- **Composable auth**: `require_admin` depends on `get_current_user` which depends on `oauth2_scheme` — a clear dependency chain.
- **Testability**: In tests, you can override `get_db` to inject a test database session.
- **Separation of concerns**: Routes don't know how to create DB sessions or decode JWTs — they just declare what they need.

**Interview tip**: _"I use Dependency Injection so that my route handlers declaratively specify what they need — a DB session, an authenticated user, an admin role — and FastAPI's DI container provides it automatically. This makes the code testable, because I can swap real dependencies with mocks."_

---

### 3.6 Singleton Pattern

**Pattern**: Ensure a class/object has only one instance throughout the application lifecycle.

**Where applied**: `app/config.py`

```python
class Settings(BaseSettings):
    SECRET_KEY: str = ...
    DATABASE_URL: str = ...
    MAX_BOOKS_PER_STUDENT: int = 3
    FINE_PER_DAY: float = 10.0
    ...

settings = Settings()   # ← Single instance, module-level
```

Also applied to:

- `engine = create_engine(...)` — one database engine
- `SessionLocal = sessionmaker(...)` — one session factory
- `Base = declarative_base()` — one ORM base class

**Why this pattern?**

- **Consistency**: Every module that imports `settings` gets the exact same configuration object.
- **Resource efficiency**: Only one DB engine/connection pool is created, not one per request.
- **Pythonic**: Python modules are naturally singletons (imported once, cached by the interpreter).

**Interview tip**: _"I use module-level singletons for configuration and database engine because these are expensive to create and must be shared. Python's import system guarantees they're instantiated only once."_

---

### 3.7 Template Method Pattern

**Pattern**: Define a skeleton algorithm in a base class, letting subclasses override specific steps.

**Where applied**: `BaseRepository` → entity-specific repositories

```python
# Base "template" — 5 generic CRUD operations
class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model    # Subclass passes its specific model
        self.db = db

    def get_by_id(self, id: int):    ...  # Generic
    def get_all(self, skip, limit):  ...  # Generic
    def create(self, obj):           ...  # Generic
    def update(self, obj):           ...  # Generic
    def delete(self, obj):           ...  # Generic

# Subclass "overrides" by EXTENDING (adding domain-specific methods)
class BookRepository(BaseRepository[Book]):
    def __init__(self, db: Session):
        super().__init__(Book, db)  # Pass model type to base

    def get_by_isbn(self, isbn):  ...  # Book-specific
    def search(self, query):      ...  # Book-specific
```

**Why this pattern?**

- **DRY (Don't Repeat Yourself)**: 5 CRUD methods × 4 entities = 20 methods written once in the base class.
- **Consistency**: All entities follow the same CRUD interface.
- **Extensibility**: Adding a new entity (e.g., `Category`) requires only a small subclass with domain-specific queries.

---

### 3.8 DTO / Data Transfer Object Pattern

**Pattern**: Use separate objects to define the shape of data crossing system boundaries (API ↔ Service).

**Where applied**: `app/schemas/`

```python
# INPUT DTO — what the client sends (validated automatically)
class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    isbn: str = Field(..., min_length=10, max_length=20)
    price: float = Field(..., gt=0)

    @field_validator("isbn")
    def validate_isbn(cls, v):
        # Custom validation: must be 13-digit number
        ...

# OUTPUT DTO — what the API returns (serialized automatically)
class BookResponse(BaseModel):
    id: int
    title: str
    available: int
    model_config = {"from_attributes": True}  # Auto-convert from ORM model

# UPDATE DTO — partial updates (all fields optional)
class BookUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
```

**Why this pattern?**

- **Security**: Internal ORM fields (e.g., `password`) are never accidentally exposed in API responses.
- **Validation at the boundary**: Invalid data is rejected before reaching business logic.
- **Decoupling**: API shape can evolve independently of the database schema.
- **Self-documenting**: Swagger/OpenAPI docs are auto-generated from these schemas.

**Interview tip**: _"DTOs act as a contract between the API and the client. The client never sees raw database models. Input DTOs validate data, output DTOs control what's exposed — this prevents data leaks and ensures API stability."_

---

### 3.9 Middleware / Chain of Responsibility Pattern

**Pattern**: Process requests through a chain of handlers, each performing a specific concern before passing to the next.

**Where applied**: `app/middleware/logging_middleware.py`

```python
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]      # 1. Generate tracking ID
        start_time = time.perf_counter()          # 2. Start timer

        response = await call_next(request)       # 3. Pass to next handler

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id  # 4. Add tracking header
        return response
```

The middleware chain in this project:

```
Request → CORS Middleware → Logging Middleware → Route Handler → Response
```

**Why this pattern?**

- **Cross-cutting concerns**: Logging, CORS, and authentication are not business logic — they apply to every request regardless of the endpoint.
- **Separation of concerns**: Route handlers don't need to log timing or add CORS headers — middleware handles it transparently.
- **Pluggable**: Adding new middleware (e.g., rate limiting, request compression) requires zero changes to existing code.

---

### 3.10 Custom Exception Hierarchy

**Pattern**: Define a hierarchy of domain-specific exceptions that map cleanly to HTTP status codes.

**Where applied**: `app/exceptions.py`

```
AppException (base → 500 Internal Server Error)
├── NotFoundError      → 404
├── ConflictError      → 409 (duplicate ISBN, username taken)
├── ValidationError    → 400 (business rule violation)
├── AuthenticationError → 401 (bad credentials/token)
└── ForbiddenError     → 403 (wrong role)
```

**Centralized handler registration:**

```python
def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def handle(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "detail": exc.message}
        )

    @app.exception_handler(Exception)
    async def catch_all(request, exc):
        return JSONResponse(status_code=500, content={...})
```

**Why this pattern?**

- **Clean error propagation**: Services throw `NotFoundError("Book", 42)` — they don't think about HTTP status codes.
- **Consistent API responses**: Every error follows the same `{"success": false, "detail": "..."}` format.
- **No try/catch in routes**: Exception handlers catch errors globally — routes stay clean.
- **Extensible**: Adding a new error type (e.g., `RateLimitError → 429`) requires only a new class — no route changes.

**Interview tip**: _"I designed a custom exception hierarchy so that business logic can express domain errors naturally (NotFoundError, ValidationError) without coupling to HTTP concepts. The global exception handler translates them to proper HTTP responses — this is a form of the Strategy Pattern for error handling."_

---

## 4. Database Design

### Entity-Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│    admins     │       │   transactions   │       │    books     │
├──────────────┤       ├──────────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)          │       │ id (PK)      │
│ username (UQ)│       │ student_id (FK)──┼──┐    │ title        │
│ password     │       │ book_id (FK)─────┼──┼──→ │ author       │
│ name         │       │ borrow_date      │  │    │ isbn (UQ)    │
│ role         │       │ due_date         │  │    │ pages        │
│ created_at   │       │ return_date      │  │    │ price        │
└──────────────┘       │ status           │  │    │ category     │
                       │ fine             │  │    │ quantity     │
┌──────────────┐       │ created_at       │  │    │ available    │
│   students   │       └──────────────────┘  │    │ created_at   │
├──────────────┤                             │    │ updated_at   │
│ id (PK)      │◄────────────────────────────┘    └──────────────┘
│ registration_│
│ username (UQ)│
│ password     │
│ name         │
│ email        │
│ phone        │
│ borrowed_bks │
│ fine_amount  │
│ created_at   │
└──────────────┘
```

### Relationships

- **Student → Transaction**: One-to-Many (a student can have many borrows)
- **Book → Transaction**: One-to-Many (a book can be borrowed many times)
- **Transaction**: Join table with additional attributes (dates, status, fine)

### Key Design Decisions

| Decision                                     | Reason                                                                              |
| -------------------------------------------- | ----------------------------------------------------------------------------------- |
| `available` column on `books`                | Avoids counting active transactions on every request (denormalized for performance) |
| `borrowed_books` on `students`               | Same — cached count for O(1) borrow-limit checks                                    |
| `status` as string enum                      | SQLite doesn't support native enums; string is portable                             |
| Soft timestamps (`created_at`, `updated_at`) | Audit trail without complex logging                                                 |

---

## 5. Interview Q&A Cheat Sheet

### Q: Why did you choose the Repository Pattern?

> "To decouple data access from business logic. If I switch databases, only repository classes change. Services and routes remain untouched. It also makes unit testing easier — I can mock repositories instead of setting up a real database."

### Q: Why not put business logic directly in routes?

> "That violates the Single Responsibility Principle. Routes should only handle HTTP concerns (parsing request, returning response). Business rules like 'a student can borrow max 3 books' belong in the service layer. This makes the logic reusable — both admin and student routes can call the same service methods."

### Q: Why JWT over session-based auth?

> "JWT is stateless — the server doesn't need to store session data. This makes horizontal scaling trivial (any server instance can validate the token). The token carries the user's role, so authorization decisions don't require additional database queries."

### Q: How does your exception handling work?

> "I have a custom exception hierarchy rooted at `AppException`. Services throw domain errors (`NotFoundError`, `ValidationError`) without knowing about HTTP. A global exception handler in FastAPI catches these and translates them to consistent JSON error responses with proper status codes. This keeps route handlers clean and error responses uniform."

### Q: Why Dependency Injection?

> "It makes the code testable and decoupled. Route handlers declare what they need (DB session, authenticated user) and FastAPI provides it. In tests, I can override these dependencies with mocks. It also handles resource lifecycle — DB sessions are automatically closed after each request."

### Q: How would you scale this system?

> "1) Switch SQLite to PostgreSQL (just change `DATABASE_URL`). 2) Run multiple Uvicorn workers behind a load balancer (JWT is stateless, so any worker can handle any request). 3) Add Redis for caching frequently-read data (book catalog). 4) If needed, extract high-traffic features (e.g., search) into separate microservices."

### Q: What SOLID principles does your code follow?

> - **S** (Single Responsibility): Routes handle HTTP, services handle logic, repos handle data.
> - **O** (Open/Closed): New entities extend `BaseRepository` without modifying it.
> - **L** (Liskov Substitution): All repositories are substitutable via the `BaseRepository` interface.
> - **I** (Interface Segregation): Schemas define minimal DTOs — clients only see what they need.
> - **D** (Dependency Inversion): Services depend on repository abstractions, not on SQLAlchemy directly.
