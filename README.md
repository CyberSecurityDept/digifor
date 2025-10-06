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

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd forenlytic-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment**
```bash
cp env.example .env
# Edit .env with your database credentials
```

5. **Initialize database**
```bash
python tools/init_db.py
```

6. **Run the server**
```bash
python scripts/run_dev.py
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