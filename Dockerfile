FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install dockerize
RUN apt-get update && apt-get install -y wget
RUN wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-v0.6.1.tar.gz
RUN tar -xzvf dockerize-linux-amd64-v0.6.1.tar.gz && mv dockerize /usr/local/bin/

# Copy the application code
COPY . .

EXPOSE 8000

# Wait for the DB to be ready and then run seed.py before starting uvicorn
CMD dockerize -wait tcp://db:5432 -timeout 30s && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 & \
    python -m app.auth.seed && \
    wait
