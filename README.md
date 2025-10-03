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

- Python 3.11+
- PostgreSQL 13+
- Redis (optional, for background tasks)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements_new.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database setup**
   ```bash
   # Create database
   createdb forenlytic
   
   # Run migrations
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   python -m app.main_new
   ```

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

## 🚀 Deployment

### Docker (Recommended)

```bash
# Build image
docker build -t forenlytic-backend .

# Run container
docker run -p 8000:8000 forenlytic-backend
```

### Manual Deployment

1. Install dependencies
2. Configure environment variables
3. Run database migrations
4. Start the application

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔄 Changelog

### v1.0.0
- Initial release
- Case management
- Evidence management
- Suspect management
- Dashboard
- Reporting
- API documentation
