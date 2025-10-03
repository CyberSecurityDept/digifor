# 🔍 Digital Forensics Analysis Platform - Backend

> **A comprehensive platform for managing digital forensics cases, evidence, and suspects with secure chain of custody tracking.**

## 🎯 What This Platform Does

This backend API helps law enforcement, government agencies, and corporate security teams manage digital forensics investigations efficiently and securely.

### 🚀 Key Features

**📁 Case Management**
- Create and track investigation cases
- Monitor case status (Open, Closed, Re-opened)
- Link cases with suspects and evidence
- Generate case statistics and reports

**🔬 Evidence Management**
- Track digital evidence with unique identifiers
- Maintain secure chain of custody records
- Store evidence metadata and file information
- Categorize evidence by type and importance

**👤 Suspect Management**
- Create detailed suspect profiles
- Manage photos and documents
- Track aliases and personal information
- Monitor suspect status and activities

**📊 Reporting & Analytics**
- Generate comprehensive case reports
- Create evidence chain documentation
- Build suspect profile reports
- Real-time dashboard with key metrics

## 🌟 Why Use This Platform?

- ✅ **Secure**: Built with security best practices
- ✅ **Compliant**: Follows digital forensics standards
- ✅ **Scalable**: Handles large volumes of cases and evidence
- ✅ **User-Friendly**: Intuitive API and documentation
- ✅ **Reliable**: Robust error handling and logging

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

### 🐳 Docker Installation (All Platforms)

#### 1. Install Docker
- **macOS**: Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)
- **Linux**: Follow [Docker installation guide](https://docs.docker.com/engine/install/)
- **Windows**: Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)

#### 2. Clone Repository
```bash
git clone https://github.com/your-username/forenlytic-backend.git
cd forenlytic-backend/backend
```

#### 3. Docker Setup
```bash
# Build the application
docker build -t forenlytic-backend .

# Run with PostgreSQL
docker-compose up -d

# Or run manually
docker run -p 8000:8000 -e DATABASE_URL=postgresql://user:pass@host:5432/db forenlytic-backend
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

### 🆘 Need Help?

If you still have problems:
1. **Check application logs**: `tail -f logs/app.log`
2. **Make sure all software is installed**: Python, PostgreSQL, Git
3. **Make sure services are running**: PostgreSQL and Redis
4. **Check .env file**: Make sure configuration is correct

---

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

---

## 🚀 Running the Application

### 🍎 Running on macOS

#### Method 1: Direct Python Execution
```bash
# Navigate to project directory
cd /path/to/forenlytic-backend/backend

# Activate virtual environment
source venv/bin/activate

# Run the application
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Method 2: Using Makefile (if available)
```bash
# Run with make
make run

# Run in development mode
make dev

# Run with specific port
make run PORT=8080
```

#### Method 3: Using Python Script
```bash
# Create a run script
cat > run_app.py << 'EOF'
#!/usr/bin/env python3
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
EOF

# Make executable and run
chmod +x run_app.py
python run_app.py
```

#### Method 4: Background Service (Production)
```bash
# Install gunicorn for production
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or with systemd service
sudo systemctl start forenlytic-backend
sudo systemctl enable forenlytic-backend
```

#### Method 5: Using Docker
```bash
# Build Docker image
docker build -t forenlytic-backend .

# Run with Docker
docker run -p 8000:8000 -e DATABASE_URL=postgresql://user:pass@host:5432/db forenlytic-backend

# Run with docker-compose
docker-compose up -d
```

---

### 🐧 Running on Linux (Ubuntu/Debian)

#### Method 1: Direct Python Execution
```bash
# Navigate to project directory
cd /path/to/forenlytic-backend/backend

# Activate virtual environment
source venv/bin/activate

# Run the application
python3 -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Method 2: Using systemd Service (Production)
```bash
# Create systemd service file
sudo nano /etc/systemd/system/forenlytic-backend.service
```

**Service file content:**
```ini
[Unit]
Description=Forenlytic Backend API
After=network.target postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/forenlytic-backend/backend
Environment=PATH=/path/to/forenlytic-backend/backend/venv/bin
ExecStart=/path/to/forenlytic-backend/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable forenlytic-backend
sudo systemctl start forenlytic-backend

# Check status
sudo systemctl status forenlytic-backend

# View logs
sudo journalctl -u forenlytic-backend -f
```

#### Method 3: Using Nginx Reverse Proxy
```bash
# Install nginx
sudo apt install nginx

# Create nginx configuration
sudo nano /etc/nginx/sites-available/forenlytic-backend
```

**Nginx configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/forenlytic-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Method 4: Using PM2 (Process Manager)
```bash
# Install PM2 globally
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'forenlytic-backend',
    script: 'venv/bin/uvicorn',
    args: 'app.main:app --host 0.0.0.0 --port 8000',
    cwd: '/path/to/forenlytic-backend/backend',
    instances: 4,
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production'
    }
  }]
}
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

### 🪟 Running on Windows

#### Method 1: Command Prompt
```cmd
# Navigate to project directory
cd C:\path\to\forenlytic-backend\backend

# Activate virtual environment
venv\Scripts\activate

# Run the application
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Method 2: PowerShell
```powershell
# Navigate to project directory
cd C:\path\to\forenlytic-backend\backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the application
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Method 3: Windows Service (Production)
```cmd
# Install NSSM (Non-Sucking Service Manager)
# Download from https://nssm.cc/download

# Create service
nssm install ForenlyticBackend
# Set path to: C:\path\to\forenlytic-backend\backend\venv\Scripts\python.exe
# Set arguments to: -m app.main
# Set working directory to: C:\path\to\forenlytic-backend\backend

# Start service
nssm start ForenlyticBackend
```

#### Method 4: Using Task Scheduler
1. Open **Task Scheduler**
2. Create **Basic Task**
3. Set trigger (e.g., at startup)
4. Set action to start program: `C:\path\to\forenlytic-backend\backend\venv\Scripts\python.exe`
5. Add arguments: `-m app.main`
6. Set working directory: `C:\path\to\forenlytic-backend\backend`

#### Method 5: Batch File
```cmd
# Create run_app.bat
@echo off
cd /d C:\path\to\forenlytic-backend\backend
call venv\Scripts\activate
python -m app.main
pause
```

#### Method 6: Using Docker Desktop
```cmd
# Build image
docker build -t forenlytic-backend .

# Run container
docker run -p 8000:8000 forenlytic-backend

# Or with docker-compose
docker-compose up -d
```

---

### 🔧 Development vs Production

#### Development Mode
```bash
# All platforms - Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

#### Production Mode
```bash
# All platforms - Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Environment-Specific Running

**Development Environment:**
```bash
# Set environment
export ENVIRONMENT=development
export DEBUG=true
export LOG_LEVEL=debug

# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production Environment:**
```bash
# Set environment
export ENVIRONMENT=production
export DEBUG=false
export LOG_LEVEL=info

# Run with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

### 📊 Monitoring and Logs

#### View Application Logs
```bash
# macOS/Linux
tail -f logs/app.log

# Windows
type logs\app.log
```

#### Monitor Application Status
```bash
# Check if application is running
curl http://localhost:8000/health

# Check API documentation
curl http://localhost:8000/docs
```

#### Performance Monitoring
   ```bash
# Monitor with htop (Linux/macOS)
htop

# Monitor with Task Manager (Windows)
# Open Task Manager and check Python processes

# Monitor with Docker
docker stats forenlytic-backend
```

---

## 📚 API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost/forenlytic` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here` |
| `DEBUG` | Debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |

### Database Configuration

The application uses PostgreSQL with SQLAlchemy ORM. Database configuration is handled through the `DATABASE_URL` environment variable.

## 🧪 Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_cases.py
```

## 📊 API Endpoints

### Case Management
- `GET /api/v1/cases` - List cases
- `POST /api/v1/cases` - Create case
- `GET /api/v1/cases/{case_id}` - Get case
- `PUT /api/v1/cases/{case_id}` - Update case
- `DELETE /api/v1/cases/{case_id}` - Delete case

### Evidence Management
- `GET /api/v1/evidence` - List evidence
- `POST /api/v1/evidence` - Create evidence
- `GET /api/v1/evidence/{evidence_id}` - Get evidence
- `PUT /api/v1/evidence/{evidence_id}` - Update evidence
- `DELETE /api/v1/evidence/{evidence_id}` - Delete evidence

### Suspect Management
- `GET /api/v1/suspects` - List suspects
- `POST /api/v1/suspects` - Create suspect
- `GET /api/v1/suspects/{person_id}` - Get suspect
- `PUT /api/v1/suspects/{person_id}` - Update suspect
- `DELETE /api/v1/suspects/{person_id}` - Delete suspect

### Dashboard
- `GET /api/v1/dashboard/overview` - Dashboard overview
- `GET /api/v1/dashboard/cases/summary` - Cases summary
- `GET /api/v1/dashboard/evidence/summary` - Evidence summary
- `GET /api/v1/dashboard/suspects/summary` - Suspects summary

### Reports
- `GET /api/v1/reports/case-summary/{case_id}` - Case summary report
- `GET /api/v1/reports/evidence-chain/{evidence_id}` - Evidence chain report
- `GET /api/v1/reports/suspect-profile/{person_id}` - Suspect profile report

## 🔒 Security

- JWT-based authentication (when implemented)
- CORS protection
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy
- File upload security

## 📈 Monitoring

- Health check endpoints
- Structured logging
- Error tracking
- Performance monitoring


### Manual Deployment

1. Install dependencies
2. Configure environment variables
3. Run database migrations
4. Start the application

