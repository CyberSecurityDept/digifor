# Complete Environment Configuration Guide

Panduan lengkap konfigurasi environment untuk Digital Forensics Backend - Development, Production, dan Security.

## 📋 **Table of Contents**

1. [Environment Files Overview](#environment-files-overview)
2. [Environment Variables Configuration](#environment-variables-configuration)
3. [Production Security Setup](#production-security-setup)
4. [PostgreSQL Database Setup](#postgresql-database-setup)
5. [Field Alias Implementation](#field-alias-implementation)
6. [Security Best Practices](#security-best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Deployment Guide](#deployment-guide)

---

## 📁 **Environment Files Overview**

### **File Structure**
```
backend/
├── .env                    # Active environment (not in git)
├── env.example            # Template for development
├── env.production         # Production template
├── env.test              # Testing template
└── docs/
    └── COMPLETE_ENVIRONMENT_GUIDE.md  # This file
```

### **File Purposes**
- **`.env`** - Active configuration (DO NOT commit to git)
- **`env.example`** - Template for new developers
- **`env.production`** - Production environment template
- **`env.test`** - Testing environment template

---

## 🔧 **Environment Variables Configuration**

### **Database Configuration**
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
DATABASE_ECHO=False

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database_name
```

### **Security Configuration**
```env
# Security - REQUIRED FOR PRODUCTION
SECRET_KEY=your-super-secure-secret-key-at-least-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENCRYPTION_KEY=your-super-secure-encryption-key-at-least-32-characters
ENCRYPTION_ALGORITHM=AES-256-GCM
```

### **File Storage**
```env
# File Storage
UPLOAD_DIR=./data/uploads
ANALYSIS_DIR=./data/analysis
REPORTS_DIR=./data/reports
MAX_FILE_SIZE=104857600  # 100MB
```

### **Logging**
```env
# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/Digital Forensics.log
```

### **API Configuration**
```env
# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Digital Forensics
VERSION=1.0.0
```

### **Development Settings**
```env
# Development
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### **Analytics**
```env
# Big Data Analytics
ANALYTICS_BATCH_SIZE=1000
HASH_ALGORITHMS=["md5", "sha1", "sha256"]
MAX_ANALYSIS_THREADS=4
```

---

## 🔒 **Production Security Setup**

### **No Default Values Approach**

Our configuration uses **NO DEFAULT VALUES** for maximum security:

```python
# config.py - Production Ready
from pydantic import Field, field_validator

class Settings(BaseSettings):
    # Database Configuration - REQUIRED FROM ENV
    database_url: str = Field(alias="DATABASE_URL")
    database_echo: bool = Field(alias="DATABASE_ECHO")
    
    # PostgreSQL specific settings - REQUIRED FROM ENV
    postgres_host: str = Field(alias="POSTGRES_HOST")
    postgres_port: int = Field(alias="POSTGRES_PORT")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(alias="POSTGRES_DB")
    
    # Security - REQUIRED FROM ENV
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(alias="ALGORITHM")
    access_token_expire_minutes: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # File Storage - REQUIRED FROM ENV
    upload_dir: str = Field(alias="UPLOAD_DIR")
    analysis_dir: str = Field(alias="ANALYSIS_DIR")
    reports_dir: str = Field(alias="REPORTS_DIR")
    max_file_size: int = Field(alias="MAX_FILE_SIZE")
    
    # Encryption - REQUIRED FROM ENV
    encryption_key: str = Field(alias="ENCRYPTION_KEY")
    encryption_algorithm: str = Field(alias="ENCRYPTION_ALGORITHM")
    
    # Logging - REQUIRED FROM ENV
    log_level: str = Field(alias="LOG_LEVEL")
    log_file: str = Field(alias="LOG_FILE")
    
    # API Configuration - REQUIRED FROM ENV
    api_v1_str: str = Field(alias="API_V1_STR")
    project_name: str = Field(alias="PROJECT_NAME")
    version: str = Field(alias="VERSION")
    
    # Development - REQUIRED FROM ENV
    debug: bool = Field(alias="DEBUG")
    cors_origins: List[str] = Field(alias="CORS_ORIGINS")
    
    # Big Data Analytics - REQUIRED FROM ENV
    analytics_batch_size: int = Field(alias="ANALYTICS_BATCH_SIZE")
    hash_algorithms: List[str] = Field(alias="HASH_ALGORITHMS")
    max_analysis_threads: int = Field(alias="MAX_ANALYSIS_THREADS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    # Field Validators for Security
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        if not v or v == "":
            raise ValueError("DATABASE_URL is required and cannot be empty")
        if not v.startswith(('postgresql://', 'sqlite://')):
            raise ValueError("DATABASE_URL must be a valid database URL")
        return v
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if not v or v == "":
            raise ValueError("SECRET_KEY is required and cannot be empty")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters for security")
        return v
    
    @field_validator('encryption_key')
    @classmethod
    def validate_encryption_key(cls, v):
        if not v or v == "":
            raise ValueError("ENCRYPTION_KEY is required and cannot be empty")
        if len(v) < 32:
            raise ValueError("ENCRYPTION_KEY must be at least 32 characters for security")
        return v
    
    @field_validator('postgres_password')
    @classmethod
    def validate_postgres_password(cls, v):
        if not v or v == "":
            raise ValueError("POSTGRES_PASSWORD is required and cannot be empty")
        if len(v) < 8:
            raise ValueError("POSTGRES_PASSWORD must be at least 8 characters")
        return v
```

### **Security Benefits**
- ✅ **No Hardcoded Values** - Semua values dari environment variables
- ✅ **Explicit Requirements** - Jelas environment variables mana yang diperlukan
- ✅ **Security Validation** - Field validators untuk keamanan
- ✅ **Fail Fast** - Aplikasi crash jika config missing

---

## 🐘 **PostgreSQL Database Setup**

### **1. Install PostgreSQL**

#### **macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

#### **Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### **Windows:**
Download and install from [PostgreSQL official website](https://www.postgresql.org/download/windows/)

### **2. Create Database and User**

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Create database user
CREATE USER your_username WITH PASSWORD 'your_password';

# Create database
CREATE DATABASE your_database_name OWNER your_username;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_username;

# Exit PostgreSQL
\q
```

### **3. Configure Environment**

```bash
# Copy template
cp env.example .env

# Edit with your PostgreSQL settings
nano .env
```

Update `.env` with your PostgreSQL configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
DATABASE_ECHO=False

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database_name
```

### **4. Run Database Setup**

```bash
# Install dependencies
pip install -r requirements.txt

# Run the PostgreSQL setup script
python tools/setup_postgres.py
```

The setup script will:
- ✅ Check PostgreSQL connection
- ✅ Create the database (if not exists)
- ✅ Create all tables
- ✅ Migrate data from SQLite (if exists)
- ✅ Create default admin user

### **5. Verify Setup**

```bash
# Test the connection
python -c "from app.database import engine; print('Database OK')"

# Or use the provided script
python tools/check_env.py
```

---

## 🔧 **Field Alias Implementation**

### **How Field Alias Works**

Field alias provides explicit mapping between environment variables and configuration fields:

```python
# Explicit mapping with Field alias
database_url: str = Field(alias="DATABASE_URL")
postgres_user: str = Field(alias="POSTGRES_USER")
secret_key: str = Field(alias="SECRET_KEY")
```

### **Mapping Table**

| Environment Variable | Field in config.py | Description |
|---------------------|-------------------|-------------|
| `DATABASE_URL` | `database_url` | Full database connection URL |
| `POSTGRES_HOST` | `postgres_host` | PostgreSQL host |
| `POSTGRES_PORT` | `postgres_port` | PostgreSQL port |
| `POSTGRES_USER` | `postgres_user` | Database username |
| `POSTGRES_PASSWORD` | `postgres_password` | Database password |
| `POSTGRES_DB` | `postgres_db` | Database name |
| `SECRET_KEY` | `secret_key` | JWT secret key |
| `ENCRYPTION_KEY` | `encryption_key` | Data encryption key |
| `DEBUG` | `debug` | Debug mode |
| `LOG_LEVEL` | `log_level` | Logging level |

### **Priority Order**
1. **Environment System Variables** (highest priority)
2. **File `.env`** (medium priority)
3. **Default values** (lowest priority - not used in production)

---

## 🔒 **Security Best Practices**

### **1. Environment Variables Security**

#### **Strong Passwords and Keys:**
```env
#  BAD - Weak credentials
SECRET_KEY=password123
POSTGRES_PASSWORD=123456

# ✅ GOOD - Strong credentials
SECRET_KEY=your-super-secure-secret-key-at-least-32-characters-long
POSTGRES_PASSWORD=your-super-secure-database-password-with-special-chars
```

#### **File Permissions:**
```bash
# Set secure permissions for .env file
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw------- 1 user user
```

### **2. Production Security**

#### **Environment Separation:**
```bash
# Development
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/dev_db

# Production
DEBUG=False
LOG_LEVEL=INFO
DATABASE_URL=postgresql://prod_user:strong_pass@prod_host:5432/prod_db
```

#### **CORS Configuration:**
```env
# Development
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Production
CORS_ORIGINS=["https://yourdomain.com", "https://api.yourdomain.com"]
```

### **3. Database Security**

#### **Connection Security:**
```env
# Use SSL for production
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Use connection pooling
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=30
```

---

## 🧪 **Testing Configuration**

### **Environment Variables Checker**

```bash
# Check all environment variables
python tools/check_env.py
```

### **Manual Testing**

```python
# Test database connection
from app.database import engine
print("Database connection successful!")

# Test configuration loading
from app.config import settings
print(f"Database URL: {settings.database_url}")
print(f"Debug mode: {settings.debug}")
```

### **Expected Behavior**
- ✅ **If all env vars exist**: Application runs normally
-  **If env vars missing**: Application crashes with clear error message

---

## 🚀 **Deployment Guide**

### **1. Development Setup**

```bash
# Clone repository
git clone <repository-url>
cd Digital Forensics-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your settings

# Setup database
python tools/setup_postgres.py

# Run application
python -m uvicorn app.main:app --reload
```

### **2. Production Deployment**

#### **Environment Variables Setup:**
```bash
# Set production environment variables
export DATABASE_URL="postgresql://prod_user:prod_pass@prod_host:5432/prod_db"
export SECRET_KEY="your-production-secret-key-32-chars-minimum"
export ENCRYPTION_KEY="your-production-encryption-key-32-chars-minimum"
export DEBUG="False"
export LOG_LEVEL="INFO"
```

#### **Docker Deployment:**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Set environment variables
ENV DATABASE_URL="postgresql://user:pass@host:5432/db"
ENV SECRET_KEY="your-production-secret-key"
ENV ENCRYPTION_KEY="your-production-encryption-key"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### **Docker Compose:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/database
      - SECRET_KEY=your-production-secret-key
      - ENCRYPTION_KEY=your-production-encryption-key
      - DEBUG=False
    ports:
      - "8000:8000"
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=your_database
      - POSTGRES_USER=your_username
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **1. Environment Variables Not Loaded**
```bash
# Check if .env file exists
ls -la .env

# Check file permissions
chmod 600 .env

# Test environment variables
python -c "from app.config import settings; print(settings.database_url)"
```

#### **2. Database Connection Error**
```bash
# Test PostgreSQL connection
psql -h localhost -U your_username -d your_database_name

# Check environment variables
python tools/check_env.py

# Test database connection
python -c "from app.database import engine; print('Database OK')"
```

#### **3. Permission Issues**
```bash
# Fix .env file permissions
chmod 600 .env

# Check file ownership
ls -la .env
```

#### **4. Missing Environment Variables**
```bash
# Check all required variables
python tools/check_env.py

# Test specific variable
python -c "from app.config import settings; print(settings.secret_key)"
```

### **Validation Errors**

#### **Secret Key Too Short:**
```
ValueError: SECRET_KEY must be at least 32 characters for security
```
**Solution:** Use a longer, stronger secret key (minimum 32 characters)

#### **Database URL Invalid:**
```
ValueError: DATABASE_URL must be a valid database URL
```
**Solution:** Ensure DATABASE_URL starts with `postgresql://` or `sqlite://`

#### **Missing Required Fields:**
```
ValueError: DATABASE_URL is required and cannot be empty
```
**Solution:** Set all required environment variables in your `.env` file

---

## 📊 **Environment Comparison**

| Setting | Development | Production | Testing |
|---------|-------------|------------|---------|
| Database | SQLite3 | PostgreSQL | SQLite3 |
| Debug | True | False | True |
| Log Level | INFO | WARNING | DEBUG |
| File Size | 100MB | 500MB | 10MB |
| Token Expiry | 30 min | 60 min | 5 min |
| CORS | Localhost | Domain | Localhost |
| Default Values | Yes | No | Yes |

---

## ✅ **Checklist**

### **Development Setup**
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment file copied (`cp env.example .env`)
- [ ] Environment variables configured
- [ ] Database setup completed (`python tools/setup_postgres.py`)
- [ ] Application runs successfully (`python -m uvicorn app.main:app --reload`)

### **Production Setup**
- [ ] All environment variables set
- [ ] Strong passwords and keys configured
- [ ] Database security configured
- [ ] File permissions set correctly (`chmod 600 .env`)
- [ ] CORS origins configured for production domain
- [ ] SSL/TLS configured for database connections
- [ ] Monitoring and logging configured

### **Security Checklist**
- [ ] No hardcoded credentials in code
- [ ] Strong secret keys (32+ characters)
- [ ] Strong database passwords (8+ characters)
- [ ] File permissions secure (600 for .env)
- [ ] Environment variables not committed to git
- [ ] Production credentials different from development
- [ ] SSL/TLS enabled for production database

---

## 🎉 **Conclusion**

This comprehensive environment configuration guide provides:

1. **Complete Environment Setup** - Development, production, and testing
2. **Security Best Practices** - No hardcoded values, strong validation
3. **PostgreSQL Integration** - Full database setup and migration
4. **Field Alias Implementation** - Explicit environment variable mapping
5. **Troubleshooting Guide** - Common issues and solutions
6. **Deployment Instructions** - Docker and production deployment

**Your Digital Forensics Backend is now production-ready with secure environment configuration!** 🔒✅
