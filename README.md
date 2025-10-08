# 🔍Digifor (digital forensik)

> **A comprehensive platform for managing digital forensics cases, evidence, suspects, and persons of interest with secure chain of custody tracking.**

## 🎯 What This Platform Does

Forenlytic is a powerful backend API designed to help law enforcement agencies, government institutions, and corporate security teams manage digital forensics investigations efficiently and securely.

### 🚀 Key Features

**📁 Case Management**
- Create and track investigation cases with unique identifiers
- Monitor case status (Open, Closed, Re-opened)
- Link cases with suspects, evidence, and persons of interest
- Generate comprehensive case statistics and reports

**🔬 Evidence Management**
- Track digital evidence with unique identifiers and hash verification
- Maintain secure chain of custody records with timestamps
- Store evidence metadata, file information, and analysis results
- Support for multiple evidence sources (HP, SSD, Harddisk, PC, Laptop, DVR)

**👤 Suspect Management**
- Create detailed suspect profiles with comprehensive information
- Track aliases, personal information, and criminal history
- Monitor suspect status and activities throughout investigations
- Risk assessment and threat level classification

**👥 Person of Interest Management**
- Add persons of interest to cases with detailed profiles
- Track custody stages (Acquisition, Preparation, Extraction, Analysis)
- Link persons with evidence and investigating officers
- Support for unknown persons and unidentified individuals

**📊 Reporting & Analytics**
- Generate comprehensive case reports with multiple templates
- Create evidence chain documentation and custody reports
- Real-time dashboard with key metrics and statistics
- Export capabilities for legal documentation

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT-based security
- **Documentation**: Auto-generated OpenAPI/Swagger
- **Testing**: Pytest with comprehensive test coverage
- **Deployment**: Docker-ready with production configurations

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- PostgreSQL 15 or higher
- Git

## 🍎 macOS Installation

### 1. Install Homebrew (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Python and PostgreSQL
```bash
# Install Python 3.11
brew install python@3.11

# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Create database
createdb forenlytic
```

### 3. Clone and Setup Project
```bash
# Clone repository
git clone https://github.com/CyberSecurityDept/digifor.git
cd digifor/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your database credentials

# Initialize database
python tools/init_db.py

# Run the server
python scripts/run_dev.py
```

## 🪟 Windows Installation

### 1. Install Python 3.11
- Download from [python.org](https://www.python.org/downloads/)
- **Important**: Check "Add Python to PATH" during installation
- Verify installation: `python --version`

### 2. Install PostgreSQL
- Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- Install with default settings
- Remember the password you set for the `postgres` user
- Open pgAdmin and create a database named `forenlytic`

### 3. Install Git
- Download from [git-scm.com](https://git-scm.com/download/win)
- Install with default settings

### 4. Clone and Setup Project
```cmd
# Clone repository
git clone https://github.com/CyberSecurityDept/digifor.git
cd digifor/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
copy env.example .env
# Edit .env with your database credentials

# Initialize database
python tools\init_db.py

# Run the server
python scripts\run_dev.py
```

## 🐧 Linux Installation (Ubuntu/Debian)

### 1. Update system packages
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Python 3.11 and pip
```bash
# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Install build essentials
sudo apt install build-essential -y
```

### 3. Install PostgreSQL
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

In PostgreSQL shell:
```sql
CREATE DATABASE forenlytic;
CREATE USER forenlytic_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE forenlytic TO forenlytic_user;
\q
```

### 4. Install Git
```bash
sudo apt install git -y
```

### 5. Clone and Setup Project
```bash
# Clone repository
git clone https://github.com/CyberSecurityDept/digifor.git
cd digifor/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your database credentials

# Initialize database
python tools/init_db.py

# Run the server
python scripts/run_dev.py
```

## 🔧 Environment Configuration

### Database Configuration (.env file)

Copy the example environment file and update the values:

```bash
# Copy environment template
cp env.example .env
```

Then edit `.env` file with your actual values:

```env
# Database Configuration
DATABASE_URL=postgresql://forenlytic_user:your_password@localhost:5432/forenlytic

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=forenlytic_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=forenlytic

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage
UPLOAD_DIR=./data/uploads
ANALYSIS_DIR=./data/analysis
REPORTS_DIR=./data/reports
MAX_FILE_SIZE=104857600  # 100MB

# Development
DEBUG=True
LOG_LEVEL=INFO
```

### Verify Installation
```bash
# Check Python version
python --version

# Check PostgreSQL connection
python tools/check_env.py

# Run tests
python tests/run_tests_new.py
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, you can access:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 📖 Documentation Files

| Document | Description | Link |
|----------|-------------|------|
| **Quick Start Guide** | 5-minute setup guide for getting started | [`docs/QUICK_START.md`](docs/QUICK_START.md) |
| **Complete Environment Guide** | Comprehensive environment configuration guide | [`docs/COMPLETE_ENVIRONMENT_GUIDE.md`](docs/COMPLETE_ENVIRONMENT_GUIDE.md) |
| **Case Management API** | Detailed API documentation for case management | [`docs/CASE_MANAGEMENT_API_DOCUMENTATION.md`](docs/CASE_MANAGEMENT_API_DOCUMENTATION.md) |
| **Authentication API** | Complete authentication API documentation | [`docs/README.md`](docs/README.md) |

## 🔧 Development

### Running Tests
```bash
python tests/run_tests_new.py
```

### Code Quality
```bash
python scripts/format.py    # Format code
python scripts/lint.py      # Lint code
python scripts/clean.py     # Clean temporary files
```

### Database Management
```bash
python scripts/setup_db.py  # Setup database
python tools/migrate_database.py  # Run migrations
```


## 🔐 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-based Access Control**: Granular permission system
- **Data Encryption**: Sensitive data encryption at rest
- **Audit Trails**: Complete activity logging and tracking
- **Chain of Custody**: Secure evidence tracking with timestamps
- **Input Validation**: Comprehensive data validation and sanitization


## 📈 Performance & Monitoring

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics`
- **Database Connection**: `GET /db/health`


**Built with ❤️ for Digital Forensics Professionals**