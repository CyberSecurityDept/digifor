# Digital Forensics Analysis Platform - Backend

Forensik digital memainkan peran penting dalam penyelidikan di berbagai konteks seperti penegakan hukum, pemerintahan, keamanan korporasi, dan ranah hukum. Platform ini hadir untuk menjawab tantangan tersebut dengan menyediakan solusi yang komprehensif, aman, dan terintegrasi untuk mengelola kasus forensik digital, barang bukti, rantai penguasaan (chain of custody), analitik lanjutan, serta pelaporan.


## 🚀 Features

### Core Modules

1. **Case Management**
   - Create, read, update, delete cases
   - Case status tracking
   - Case-person associations
   - Case statistics

2. **Evidence Management**
   - Evidence tracking and cataloging
   - Chain of custody management
   - Evidence metadata
   - Evidence type management

3. **Suspect Management**
   - Person profiles
   - Photo management
   - Document management
   - Alias management

4. **Reporting**
   - Case reports
   - Evidence chain reports
   - Suspect profiles
   - Analytics dashboard

5. **Dashboard**
   - Overview statistics
   - Module-specific summaries
   - Real-time data

## 🛠️ Installation

### Prerequisites

- **Python 3.11+** (Required)
- **PostgreSQL 13+** (Required)
- **Git** (Required)
- **Redis** (Optional, for background tasks)

### 🍎 macOS Installation

#### 1. Install Prerequisites

**Install Homebrew (if not already installed):**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Install Python 3.11+ and PostgreSQL:**
```bash
# Install Python
brew install python@3.11

# Install PostgreSQL
brew install postgresql@13

# Start PostgreSQL service
brew services start postgresql@13

# Install Redis (optional)
brew install redis
brew services start redis
```

#### 2. Clone Repository
```bash
# Clone the repository
git clone https://github.com/your-username/forenlytic-backend.git
cd forenlytic-backend/backend

# Verify you're in the correct directory
ls -la
```

#### 3. Setup Python Environment
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### 4. Install Dependencies
```bash
# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

#### 5. Database Setup
```bash
# Create PostgreSQL database
createdb forenlytic

# Or using psql
psql -U postgres -c "CREATE DATABASE forenlytic;"

# Run database setup script
python tools/setup_postgres.py
```

#### 6. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit environment variables
nano .env
```

**Required .env configuration:**
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/forenlytic
SECRET_KEY=your-secret-key-here
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

#### 7. Run Application
```bash
# Start the application
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 🐧 Linux Installation (Ubuntu/Debian)

#### 1. Install Prerequisites

**Update system packages:**
```bash
sudo apt update && sudo apt upgrade -y
```

**Install Python 3.11+ and PostgreSQL:**
```bash
# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib postgresql-client

# Install Redis (optional)
sudo apt install redis-server

# Install Git
sudo apt install git

# Install build essentials
sudo apt install build-essential
```

**Start services:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### 2. Clone Repository
```bash
# Clone the repository
git clone https://github.com/your-username/forenlytic-backend.git
cd forenlytic-backend/backend

# Verify you're in the correct directory
ls -la
```

#### 3. Setup Python Environment
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### 4. Install Dependencies
```bash
# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

#### 5. Database Setup
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE forenlytic;
CREATE USER forenlytic_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE forenlytic TO forenlytic_user;
\q

# Run database setup script
python tools/setup_postgres.py
```

#### 6. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit environment variables
nano .env
```

**Required .env configuration:**
```env
DATABASE_URL=postgresql://forenlytic_user:your_password@localhost:5432/forenlytic
SECRET_KEY=your-secret-key-here
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

#### 7. Run Application
```bash
# Start the application
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 🪟 Windows Installation

#### 1. Install Prerequisites

**Install Python 3.11+:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

**Install PostgreSQL:**
1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Install with default settings
3. Remember the password you set for the postgres user
4. Add PostgreSQL to PATH (usually `C:\Program Files\PostgreSQL\13\bin`)

**Install Git:**
1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Install with default settings

**Install Redis (Optional):**
1. Download Redis from [github.com/microsoftarchive/redis](https://github.com/microsoftarchive/redis/releases)
2. Extract and run `redis-server.exe`

#### 2. Clone Repository
```cmd
# Clone the repository
git clone https://github.com/your-username/forenlytic-backend.git
cd forenlytic-backend\backend

# Verify you're in the correct directory
dir
```

#### 3. Setup Python Environment
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

#### 4. Install Dependencies
```cmd
# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

#### 5. Database Setup
```cmd
# Create database using psql
psql -U postgres -c "CREATE DATABASE forenlytic;"

# Or using pgAdmin (GUI)
# 1. Open pgAdmin
# 2. Connect to PostgreSQL server
# 3. Right-click "Databases" → "Create" → "Database"
# 4. Name: forenlytic

# Run database setup script
python tools\setup_postgres.py
```

#### 6. Environment Configuration
```cmd
# Copy environment template
copy env.example .env

# Edit environment variables (use Notepad or VS Code)
notepad .env
```

**Required .env configuration:**
```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/forenlytic
SECRET_KEY=your-secret-key-here
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

#### 7. Run Application
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

### ✅ Verification

After installation, verify everything is working:

1. **Check API Health:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Access Documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Test Database Connection:**
   ```bash
   python -c "from app.db.session import engine; print('Database connected successfully')"
   ```

### 🔧 Troubleshooting

#### Common Issues:

1. **Python version issues:**
   ```bash
   # Check Python version
   python --version
   # Should be 3.11 or higher
   ```

2. **PostgreSQL connection issues:**
   ```bash
   # Test PostgreSQL connection
   psql -U postgres -c "SELECT version();"
   ```

3. **Permission issues (Linux/macOS):**
   ```bash
   # Fix PostgreSQL permissions
   sudo -u postgres psql
   ALTER USER postgres PASSWORD 'your_password';
   ```

4. **Windows PATH issues:**
   - Add PostgreSQL bin directory to Windows PATH
   - Restart command prompt after PATH changes

5. **Virtual environment issues:**
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate  # Windows
   ```

### 📞 Support

If you encounter issues:
1. Check the logs: `tail -f logs/app.log`
2. Verify all prerequisites are installed
3. Ensure all services are running
4. Check environment variables in `.env`

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

