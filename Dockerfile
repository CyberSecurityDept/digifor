# Gunakan base image Python
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua source code
COPY . .

# Expose port (misalnya FastAPI/uvicorn di 8000)
EXPOSE 8000

# Jalankan aplikasi (ubah sesuai entrypoint kamu)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
