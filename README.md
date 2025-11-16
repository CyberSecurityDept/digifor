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
  # Activate virtual environment first
  source venv/bin/activate  # macOS/Linux
  venv\Scripts\activate     # Windows
  
  # Check current migration status
  alembic current
  
  # Apply all pending migrations
  alembic upgrade head
  
  # View migration history
  alembic history
  
  # Rollback to previous migration (if needed)
  alembic downgrade -1
  
  # Create new migration (after model changes)
  alembic revision --autogenerate -m "description_of_changes"
  alembic upgrade head
  ```
- **Database Initialization**: Use the provided script to set up the database
  ```bash
  python tools/setup_postgres.py
  ```
- **Backup**: Regular backups recommended for production environments

### Alembic Migration Setup

This project uses Alembic for database schema versioning and migrations. The Alembic configuration is located in:
- `alembic.ini` - Main Alembic configuration file
- `alembic/env.py` - Environment configuration for migrations
- `alembic/versions/` - Directory containing migration scripts

**Important Migration Files:**
- Migration files in `alembic/versions/` should be committed to version control
- All developers should run `alembic upgrade head` after pulling new migrations
- Never edit existing migration files that have been applied to production

**Creating New Migrations:**
```bash
# After modifying models, create a new migration
alembic revision --autogenerate -m "description_of_changes"

# Review the generated migration file
# Then apply it
alembic upgrade head
```

**Migration Best Practices:**
1. Always review auto-generated migrations before applying
2. Test migrations on a development database first
3. Create backups before running migrations in production
4. Keep migration files in version control
5. Document breaking changes in migration comments

## 🔴 Redis Server

### Why Redis?

Redis is used as a message broker for Celery task queue and for caching purposes in this platform:

- **Task Queue**: Celery uses Redis as a message broker to handle asynchronous tasks
- **Caching**: Fast in-memory data storage for frequently accessed data
- **Performance**: Sub-millisecond latency for data operations
- **Persistence**: Optional persistence to disk for data durability
- **Scalability**: Supports master-slave replication and clustering

### Redis Installation (Ubuntu/Debian)

#### Install Redis Server

```bash
# Update package list
sudo apt update

# Install Redis Server
sudo apt install redis-server -y
```

#### Start and Enable Redis Service

```bash
# Start Redis service
sudo systemctl start redis-server

# Enable Redis to start on boot
sudo systemctl enable redis-server

# Check Redis status
sudo systemctl status redis-server
```

#### Verify Redis Installation

```bash
# Test Redis connection
redis-cli ping
# Should return: PONG

# Check Redis version
redis-cli --version
```

#### View Redis Logs

```bash
# View recent Redis logs (last 30 lines)
sudo journalctl -u redis-server --no-pager -n 30

# Follow Redis logs in real-time
sudo journalctl -u redis-server -f
```

#### Redis Service Management

```bash
# Check Redis service status
sudo systemctl status redis-server

# Restart Redis service
sudo systemctl restart redis-server

# Stop Redis service
sudo systemctl stop redis-server

# Start Redis service
sudo systemctl start redis-server
```

### Redis Configuration

Redis configuration file is located at `/etc/redis/redis.conf`. You can modify settings such as:

- **Port**: Default is 6379
- **Bind Address**: Default is 127.0.0.1 (localhost)
- **Password**: Optional authentication
- **Persistence**: RDB snapshots and AOF logging

To edit Redis configuration:

```bash
sudo nano /etc/redis/redis.conf
```

After modifying configuration, restart Redis:

```bash
sudo systemctl restart redis-server
```

### Redis Usage in This Platform

Redis is used for:

1. **Celery Message Broker**: Handles asynchronous task queue for background jobs
2. **Caching**: Stores frequently accessed data for faster retrieval
3. **Session Storage**: Optional session management (if configured)

### Troubleshooting Redis

**Redis service not starting:**
```bash
# Check Redis logs for errors
sudo journalctl -u redis-server -n 50

# Verify Redis configuration
sudo redis-server --test-memory 1
```

**Redis connection refused:**
```bash
# Check if Redis is running
sudo systemctl status redis-server

# Verify Redis is listening on correct port
sudo netstat -tlnp | grep 6379
# or
sudo ss -tlnp | grep 6379
```

**Redis permission denied:**
```bash
# Check Redis socket permissions
ls -la /var/run/redis/

# Fix permissions if needed
sudo chown redis:redis /var/run/redis/redis-server.sock
sudo chmod 755 /var/run/redis/
```



## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis Server (for Celery task queue and caching)
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
python tools/setup_postgres.py

# 9. Run database migrations
alembic upgrade head

# 10. Run server
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
python tools\setup_postgres.py

# 10. Run database migrations
alembic upgrade head

# 11. Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 🐧 Linux (Ubuntu/Debian)

```bash
# 1. Install dependencies
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip postgresql postgresql-contrib git build-essential -y

# 2. Install Redis Server (for Celery task queue)
sudo apt install redis-server -y

# 3. Start PostgreSQL and Redis services
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 4. Verify Redis is running
sudo systemctl status redis-server

# 5. Create database and user
sudo -u postgres psql -c "CREATE DATABASE forenlytic;"
sudo -u postgres psql -c "CREATE USER forenlytic_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE forenlytic TO forenlytic_user;"

# 6. Clone project
git clone https://github.com/CyberSecurityDept/digifor.git
cd digifor/backend

# 7. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 8. Install dependencies
pip install -r requirements.txt

# 9. Setup environment
cp env.example .env
# Edit .env file with your database credentials

# 10. Initialize database
python tools/setup_postgres.py

# 11. Run database migrations
alembic upgrade head

# 12. Run server
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

**Error: Redis connection failed**
```bash
# Pastikan Redis sedang berjalan
sudo systemctl status redis-server

# Start Redis jika belum berjalan
sudo systemctl start redis-server

# Cek Redis logs untuk error
sudo journalctl -u redis-server --no-pager -n 30
```

**Error: Port already in use**
```bash
# Gunakan port lain
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

API akan tersedia di `http://localhost:8000`

## 🚀 Setup Awal dan Menjalankan Service (Linux)

### Langkah Setup Awal (hanya sekali)

**Aktifkan virtual environment:**

```bash
cd /home/digifor/digifor-v2
source venv/bin/activate
```

**Install dependencies:**

```bash
pip install --upgrade -r requirements.txt
```

**Cek DB & inisialisasi:**

```bash
python scripts/check-db-connection.py
python scripts/init-database.py

# Run database migrations
alembic upgrade head

# Seed initial data
python -m app.auth.seed
```

### Menjalankan Service

Setelah setup awal selesai:

```bash
sudo systemctl daemon-reload        # reload systemd
sudo systemctl enable digifor-v2    # auto-start saat boot (opsional)
sudo systemctl start digifor-v2
sudo systemctl status digifor-v2
```

Untuk informasi lebih detail tentang systemd service, lihat dokumentasi di [`docs/SYSTEMD_SERVICE.md`](docs/SYSTEMD_SERVICE.md).

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