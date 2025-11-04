# 🔍Digifor (digital forensik)

> **A comprehensive platform for managing digital forensics cases, evidence, suspects, and persons of interest with secure chain of custody tracking. Includes advanced analytics capabilities for contact correlation, hashfile analysis, social media correlation, deep communication analysis, APK analysis, and secure file encryption.**

## 🎯 What This Platform Does

Forenlytic is a powerful backend API designed to help law enforcement agencies, government institutions, and corporate security teams manage digital forensics investigations efficiently and securely. The platform provides three main modules:

**📁 Case Management**
- **Cases**: Create and manage investigation cases with comprehensive tracking
- **Evidence**: Track digital evidence with secure chain of custody and hash verification
- **Suspect**: Manage suspect profiles and link them to cases and evidence

**Analytics**
- **Contact Correlation**: Analyze and correlate contact information across multiple sources
- **Hashfile Analytics**: Process and analyze hash files from various forensic tools
- **Social Media Correlation**: Extract and correlate social media data and communications
- **Deep Communication Analytics**: Advanced analysis of communication patterns and threads
- **APK Analysis**: Analyze Android APK files for forensic investigation

**🔐 File Encryptor**
- Convert original files into encrypted format for secure storage and transmission
- Protect sensitive forensic data with encryption before sharing or archiving

## 🛠️ Technology Stack

### Core Framework
- **Backend Framework**: FastAPI 0.120.4 (Python 3.11+)
- **ASGI Server**: Uvicorn 0.38.0 with uvloop
- **Language**: Python 3.11+

### Database & ORM
- **Database**: PostgreSQL 15+
  - Open-source relational database management system
  - ACID-compliant with robust data integrity
  - Supports complex queries, JSON data types, and full-text search
  - Excellent performance for large-scale forensic data
  - Built-in support for concurrent connections and transactions
- **ORM**: SQLAlchemy 2.0.44
  - Modern Python SQL toolkit and ORM
  - Type-safe query building and relationship management
  - Connection pooling and session management
- **Database Driver**: psycopg2-binary 2.9.11
  - PostgreSQL adapter for Python
  - Binary package for easy installation
  - Supports all PostgreSQL features and data types
- **Migrations**: Alembic 1.17.1
  - Database migration tool integrated with SQLAlchemy
  - Version control for database schema changes
  - Automatic migration generation and rollback support

### Authentication & Security
- **Authentication**: JWT-based security (python-jose 3.5.0)
- **Password Hashing**: Passlib 1.7.4 with bcrypt 4.1.2
- **Encryption**: Cryptography 46.0.3
- **Email Validation**: email-validator 2.2.0

### Data Processing & Analytics
- **Data Analysis**: Pandas 2.3.3, NumPy 2.3.4
- **Excel Processing**: OpenPyXL 3.1.5, xlrd 2.0.2
- **File Type Detection**: python-magic 0.4.27
- **Image Processing**: Pillow 12.0.0

### Task Queue & Caching
- **Task Queue**: Celery 5.5.3
- **Message Broker**: Redis 7.0.1
- **AMQP**: Kombu 5.5.4

### Document Generation
- **PDF Generation**: ReportLab 4.4.4

### API Documentation
- **Documentation**: Auto-generated OpenAPI/Swagger
- **API Testing**: Postman collections included

### Development & Testing
- **Testing**: Pytest with comprehensive test coverage
- **Code Quality**: Flake8 6.1.0
- **Logging**: Structlog 25.5.0
- **Environment Management**: python-dotenv 1.2.1

### Deployment
- **Production Ready**: Docker-ready with production configurations
- **Monitoring**: Prometheus client 0.23.1

## 🗄️ PostgreSQL Database

### Why PostgreSQL?

PostgreSQL is chosen as the primary database for this platform due to its:

- **Reliability & Data Integrity**: ACID-compliant transactions ensure data consistency for critical forensic evidence
- **Performance**: Optimized for handling large datasets common in digital forensics investigations
- **Advanced Features**: 
  - JSON/JSONB support for flexible data storage
  - Full-text search capabilities
  - Array data types for complex data structures
  - Advanced indexing (B-tree, Hash, GiST, GIN, BRIN)
- **Scalability**: Handles concurrent connections and high transaction volumes
- **Extensibility**: Support for custom functions, operators, and data types
- **Security**: Row-level security, encryption at rest, and comprehensive access controls

### Database Configuration

The platform uses PostgreSQL 15+ with the following default configuration:

```env
# PostgreSQL Connection Settings
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=forenlytic_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=forenlytic

# Database URL (alternative format)
DATABASE_URL=postgresql://forenlytic_user:your_password@localhost:5432/forenlytic
```

### Database Features Used

- **Connection Pooling**: SQLAlchemy manages connection pools for efficient database access
- **Transactions**: All database operations are wrapped in transactions for data integrity
- **Migrations**: Alembic handles schema versioning and database migrations
- **Relationships**: Complex relationships between cases, evidence, suspects, and analytics data
- **Indexes**: Optimized indexes for fast query performance on large datasets
- **Constraints**: Foreign keys, unique constraints, and check constraints ensure data consistency

### Performance Considerations

- **Connection Pooling**: Configured through SQLAlchemy for optimal connection management
- **Query Optimization**: Efficient queries with proper indexing on frequently accessed columns
- **Batch Processing**: Large data imports use batch operations for better performance
- **Async Support**: Ready for async database operations with FastAPI

### Database Management

- **Migrations**: Run migrations using Alembic
  ```bash
  alembic upgrade head
  ```
- **Database Initialization**: Use the provided script to set up the database
  ```bash
  python tools/init_db.py
  ```
- **Backup**: Regular backups recommended for production environments



## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Git

### Installation Steps

#### 🍎 macOS

```bash
# 1. Install dependencies (if not installed)
brew install python@3.11 postgresql@15 git

# 2. Start PostgreSQL
brew services start postgresql@15

# 3. Create database
createdb forenlytic

# 4. Clone project
git clone https://github.com/CyberSecurityDept/digifor.git
cd digifor/backend

# 5. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install -r requirements.txt

# 7. Setup environment
cp env.example .env
# Edit .env file with your database credentials

# 8. Initialize database
python tools/init_db.py

# 9. Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 🪟 Windows

```cmd
# 1. Install Python 3.11+ from python.org (check "Add to PATH")
# 2. Install PostgreSQL from postgresql.org
# 3. Install Git from git-scm.com
# 4. Open pgAdmin and create database named 'forenlytic'

# 5. Clone project
git clone https://github.com/CyberSecurityDept/digifor.git
cd digifor\backend

# 6. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 7. Install dependencies
pip install -r requirements.txt

# 8. Setup environment
copy env.example .env
# Edit .env file with your database credentials

# 9. Initialize database
python tools\init_db.py

# 10. Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 🐧 Linux (Ubuntu/Debian)

```bash
# 1. Install dependencies
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip postgresql postgresql-contrib git build-essential -y

# 2. Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 3. Create database and user
sudo -u postgres psql -c "CREATE DATABASE forenlytic;"
sudo -u postgres psql -c "CREATE USER forenlytic_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE forenlytic TO forenlytic_user;"

# 4. Clone project
git clone https://github.com/CyberSecurityDept/digifor.git
cd digifor/backend

# 5. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install -r requirements.txt

# 7. Setup environment
cp env.example .env
# Edit .env file with your database credentials

# 8. Initialize database
python tools/init_db.py

# 9. Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Configuration

Edit `.env` file with your database credentials:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=forenlytic_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=forenlytic
DATABASE_URL=postgresql://forenlytic_user:your_password@localhost:5432/forenlytic
```

### Troubleshooting

**Error: ModuleNotFoundError**
```bash
# Pastikan virtual environment aktif
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install ulang dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Error: Database connection failed**
- Pastikan PostgreSQL sedang berjalan
- Cek kredensial di file `.env`
- Verifikasi database sudah dibuat

**Error: Port already in use**
```bash
# Gunakan port lain
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

API akan tersedia di `http://localhost:8000`

## 📚 API Documentation

Once the server is running, you can access:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 📖 Documentation Files

| Document | Description | Link |
|----------|-------------|------|
| **Case Management API** | Detailed API documentation for case management | [`docs/CASE_MANAGEMENT_API_DOCUMENTATION.md`](docs/CASE_MANAGEMENT_API_DOCUMENTATION.md) |
| **Analytics API** | Complete analytics API documentation (Contact Correlation, Hashfile Analytics, Social Media Correlation, Deep Communication Analytics, APK Analysis) | [`docs/Digital_Forensics_API_Contract_Analytics.md`](docs/Digital_Forensics_API_Contract_Analytics.md) |



** Digital Forensics **