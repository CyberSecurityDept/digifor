# 🔍 Digital Forensics Analysis Platform - Backend

> **A comprehensive platform for managing digital forensics cases, evidence, suspects, and persons of interest with secure chain of custody tracking.**

## 🎯 What This Platform Does

This backend API helps law enforcement, government agencies, and corporate security teams manage digital forensics investigations efficiently and securely.

### 🚀 Key Features

**📁 Case Management**
- Create and track investigation cases
- Monitor case status (Open, Closed, Re-opened)
- Link cases with suspects, evidence, and persons of interest
- Generate case statistics and reports
- Case logs and notes management

**🔬 Evidence Management**
- Track digital evidence with unique identifiers
- Maintain secure chain of custody records
- Store evidence metadata and file information
- Categorize evidence by type and importance
- Evidence analysis and processing tracking

**👤 Suspect Management**
- Create detailed suspect profiles
- Manage photos and documents
- Track aliases and personal information
- Monitor suspect status and activities
- Risk assessment and criminal record tracking

**👥 Person of Interest Management**
- Add persons of interest to cases
- Track custody stages (Acquisition, Preparation, Extraction, Analysis)
- Link persons with evidence and investigators
- Support for unknown persons
- Evidence source tracking (HP, SSD, Harddisk, PC, Laptop, DVR)

**📊 Reporting & Analytics**
- Generate comprehensive case reports
- Create evidence chain documentation
- Build suspect profile reports
- Real-time dashboard with key metrics


## 🚀 Quick Start

### What You Need Before Starting

Make sure you have these installed on your computer:

- **Python 3.11 or newer** ✅ (Required)
- **PostgreSQL 13 or newer** ✅ (Required) 
- **Git** ✅ (Required)
- **Redis** ⚠️ (Optional, for background tasks)

> 💡 **Don't have these?** Follow the installation guide below for your operating system.

### 🍎 For macOS Users

#### Step 1: Install Homebrew (if you don't have it)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Step 2: Install Python and PostgreSQL
   ```bash
# Install Python
brew install python@3.11

# Install PostgreSQL
brew install postgresql@13

# Start PostgreSQL
brew services start postgresql@13

# Install Redis (optional)
brew install redis
brew services start redis
```

#### Step 3: Download the Code
   ```bash
# Download code from GitHub
git clone https://github.com/your-username/forenlytic-backend.git
cd forenlytic-backend/backend

# Make sure you're in the right folder
ls -la
```

#### Step 4: Setup Python Environment
   ```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Update pip
pip install --upgrade pip
```

#### Step 5: Install Required Packages
   ```bash
# Install all required packages
pip install -r requirements.txt

# Check if everything installed correctly
pip list
```

#### Step 6: Setup Database
   ```bash
# Create PostgreSQL database
   createdb forenlytic
   
# Or using psql
psql -U postgres -c "CREATE DATABASE forenlytic;"

# Setup database tables
python tools/setup_postgres.py
```

#### Step 7: Configure Environment
```bash
# Copy configuration file
cp env.example .env

# Edit configuration
nano .env
```

**Fill your .env file like this:**
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/forenlytic
SECRET_KEY=your-secret-key-here
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

#### Step 8: Run the Application
```bash
# Start the application
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 🐧 For Linux Users (Ubuntu/Debian)

#### Step 1: Update Your System
```bash
sudo apt update && sudo apt upgrade -y
```

#### Step 2: Install Python and PostgreSQL
```bash
# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib postgresql-client

# Install Redis (optional)
sudo apt install redis-server

# Install Git
sudo apt install git

# Install build tools
sudo apt install build-essential
```

#### Step 3: Start Services
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Step 4: Download the Code
```bash
# Download code from GitHub
git clone https://github.com/your-username/forenlytic-backend.git
cd forenlytic-backend/backend

# Make sure you're in the right folder
ls -la
```

#### Step 5: Setup Python Environment
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Update pip
pip install --upgrade pip
```

#### Step 6: Install Required Packages
```bash
# Install all required packages
pip install -r requirements.txt

# Check if everything installed correctly
pip list
```

#### Step 7: Setup Database
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE forenlytic;
CREATE USER forenlytic_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE forenlytic TO forenlytic_user;
\q

# Setup database tables
python tools/setup_postgres.py
```

#### Step 8: Configure Environment
```bash
# Copy configuration file
cp env.example .env

# Edit configuration
nano .env
```

**Fill your .env file like this:**
```env
DATABASE_URL=postgresql://forenlytic_user:your_password@localhost:5432/forenlytic
SECRET_KEY=your-secret-key-here
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

#### Step 9: Run the Application
```bash
# Start the application
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 🪟 For Windows Users

#### Step 1: Install Python
1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation, **check "Add Python to PATH"**
3. Test installation:
   ```cmd
   python --version
   pip --version
   ```

#### Step 2: Install PostgreSQL
1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Install with default settings
3. **Remember the password** you set for the postgres user
4. Add PostgreSQL to PATH (usually `C:\Program Files\PostgreSQL\13\bin`)

#### Step 3: Install Git
1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Install with default settings

#### Step 4: Install Redis (Optional)
1. Download Redis from [github.com/microsoftarchive/redis](https://github.com/microsoftarchive/redis/releases)
2. Extract and run `redis-server.exe`

#### Step 5: Download the Code
```cmd
# Download code from GitHub
git clone https://github.com/your-username/forenlytic-backend.git
cd forenlytic-backend\backend

# Make sure you're in the right folder
dir
```

#### Step 6: Setup Python Environment
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Update pip
python -m pip install --upgrade pip
```

#### Step 7: Install Required Packages
```cmd
# Install all required packages
pip install -r requirements.txt

# Check if everything installed correctly
pip list
```

#### Step 8: Setup Database
```cmd
# Create database using psql
psql -U postgres -c "CREATE DATABASE forenlytic;"

# Or using pgAdmin (GUI)
# 1. Open pgAdmin
# 2. Connect to PostgreSQL server
# 3. Right-click "Databases" → "Create" → "Database"
# 4. Name: forenlytic

# Setup database tables
python tools\setup_postgres.py
```

#### Step 9: Configure Environment
```cmd
# Copy configuration file
copy env.example .env

# Edit configuration (use Notepad or VS Code)
notepad .env
```

**Fill your .env file like this:**
```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/forenlytic
SECRET_KEY=your-secret-key-here
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

#### Step 10: Run the Application
```cmd
# Start the application
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---


## ✅ Check if Everything Works

After installation, make sure everything is working properly:

### 1. Test API Health
```bash
curl http://localhost:8000/health
```
**Expected result**: JSON response with status "healthy"

### 2. Open API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Test Database Connection
```bash
python -c "from app.db.session import engine; print('Database connected successfully')"
```
**Expected result**: "Database connected successfully"

---

## 🔧 Fix Common Problems

### ❌ Common Issues and Solutions

#### 1. **Error: Python version is wrong**
```bash
# Check Python version
python --version
# Should be 3.11 or higher
```

#### 2. **Error: Can't connect to PostgreSQL**
```bash
# Test PostgreSQL connection
psql -U postgres -c "SELECT version();"
```

#### 3. **Error: Permission denied (Linux/macOS)**
```bash
# Fix PostgreSQL permissions
sudo -u postgres psql
ALTER USER postgres PASSWORD 'your_password';
```

#### 4. **Error: Command not found (Windows)**
- Add PostgreSQL bin directory to Windows PATH
- Restart command prompt after changing PATH

#### 5. **Error: Virtual environment is broken**
```bash
# Delete and recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

## 🎯 How to Use the Platform

### 1. **Access the Application**
- Open your browser and go to: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 2. **Test the API**
```bash
# Test health check
curl http://localhost:8000/health

# Test get cases
curl http://localhost:8000/api/v1/cases/get-all-cases
```

### 3. **Stop the Application**
- Press `Ctrl + C` in the terminal
- Or close the terminal

## 🚀 How to Run the Application

### Basic Running (All Platforms)
```bash
# Navigate to project directory
cd /path/to/forenlytic-backend/backend

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Run the application
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Running
   ```bash
# For production with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

---

## 📚 API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 🔗 Available API Endpoints

**Case Management**
- `POST /api/v1/cases/create-case` - Create new case
- `GET /api/v1/cases/get-case-detail/{case_id}` - Get case details
- `GET /api/v1/cases/get-all-cases` - List all cases
- `PUT /api/v1/cases/update-case/{case_id}` - Update case
- `DELETE /api/v1/cases/delete-case/{case_id}` - Delete case
- `GET /api/v1/cases/statistics/summary` - Get case statistics

**Case Logs**
- `POST /api/v1/case-logs/create-log` - Create case log
- `GET /api/v1/case-logs/get-case-logs/{case_id}` - Get case logs

**Case Notes**
- `POST /api/v1/case-notes/create-note` - Create case note
- `GET /api/v1/case-notes/get-case-notes/{case_id}` - Get case notes
- `PUT /api/v1/case-notes/update-note/{note_id}` - Update note
- `DELETE /api/v1/case-notes/delete-note/{note_id}` - Delete note

**Person of Interest Management**
- `POST /api/v1/persons/create-person` - Create person of interest
- `GET /api/v1/persons/get-person/{person_id}` - Get person details
- `GET /api/v1/persons/get-persons-by-case/{case_id}` - Get persons by case
- `PUT /api/v1/persons/update-person/{person_id}` - Update person
- `DELETE /api/v1/persons/delete-person/{person_id}` - Delete person

**Evidence Management**
- `POST /api/v1/evidence/create-evidence` - Create evidence
- `GET /api/v1/evidence/get-evidence/{evidence_id}` - Get evidence details
- `GET /api/v1/evidence/get-evidence-by-case/{case_id}` - Get evidence by case
- `PUT /api/v1/evidence/update-evidence/{evidence_id}` - Update evidence
- `DELETE /api/v1/evidence/delete-evidence/{evidence_id}` - Delete evidence

**Suspect Management**
- `POST /api/v1/suspects/create-suspect` - Create suspect
- `GET /api/v1/suspects/get-suspect/{suspect_id}` - Get suspect details
- `GET /api/v1/suspects/get-all-suspects` - List all suspects
- `PUT /api/v1/suspects/update-suspect/{suspect_id}` - Update suspect
- `DELETE /api/v1/suspects/delete-suspect/{suspect_id}` - Delete suspect

**Reports**
- `GET /api/v1/reports/generate-case-report/{case_id}` - Generate case report
- `GET /api/v1/reports/generate-evidence-report/{evidence_id}` - Generate evidence report
- `GET /api/v1/reports/generate-suspect-report/{suspect_id}` - Generate suspect report

**Dashboard**
- `GET /api/v1/dashboard/statistics` - Get dashboard statistics
- `GET /api/v1/dashboard/recent-cases` - Get recent cases
- `GET /api/v1/dashboard/evidence-summary` - Get evidence summary

## 🗄️ Database Structure

The platform uses PostgreSQL with the following main tables:

**Core Tables**
- `cases` - Investigation cases
- `persons` - Persons of interest linked to cases
- `suspects` - Suspect profiles
- `evidence` - Digital evidence items
- `agencies` - Law enforcement agencies
- `work_units` - Agency work units

**Supporting Tables**
- `case_logs` - Case activity logs
- `case_notes` - Case notes and comments
- `custody_logs` - Evidence chain of custody
- `custody_reports` - Custody documentation
- `evidence_types` - Evidence categorization

## 📝 Example Usage

### Creating a Case with Person of Interest

```bash
# 1. Create a new case
curl -X POST "http://localhost:8000/api/v1/cases/create-case" \
  -H "Content-Type: application/json" \
  -d '{
    "case_number": "CASE-2024-001",
    "title": "Digital Forensics Investigation",
    "description": "Investigation of digital evidence",
    "main_investigator": "Detective Smith"
  }'

# 2. Add person of interest to the case
curl -X POST "http://localhost:8000/api/v1/persons/create-person" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": 1,
    "name": "John Doe",
    "is_unknown": false,
    "custody_stage": "Acquisition",
    "evidence_id": "EVID-001",
    "evidence_source": "HP",
    "evidence_summary": "GPS data from suspect phone",
    "investigator": "Detective Smith",
    "created_by": "Admin"
  }'

# 3. Get all persons for the case
curl -X GET "http://localhost:8000/api/v1/persons/get-persons-by-case/1"
```

### Person of Interest Data Structure

```json
{
  "id": 1,
  "name": "John Doe",
  "is_unknown": false,
  "custody_stage": "Acquisition",
  "evidence_id": "EVID-001",
  "evidence_source": "HP",
  "evidence_summary": "GPS data from suspect phone",
  "investigator": "Detective Smith",
  "case_id": 1,
  "created_by": "Admin",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost/forenlytic` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here` |
| `DEBUG` | Debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |

## 🚀 Recent Updates

### v1.2.0 - Person of Interest Management
- ✅ Added Person of Interest management system
- ✅ Support for unknown persons
- ✅ Custody stage tracking (Acquisition, Preparation, Extraction, Analysis)
- ✅ Evidence source tracking (HP, SSD, Harddisk, PC, Laptop, DVR)
- ✅ Complete CRUD operations for persons
- ✅ Integration with case management system

### v1.1.0 - Enhanced Case Management
- ✅ Case logs and notes system
- ✅ Improved case statistics
- ✅ Better error handling
- ✅ Enhanced API documentation

### v1.0.0 - Initial Release
- ✅ Core case management
- ✅ Evidence tracking
- ✅ Suspect management
- ✅ Basic reporting


